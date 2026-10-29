"""
Care AI Engine - NHS MCP Server v3
Model Context Protocol server that provides LIVE NHS medical data.

v3 changes:
  - Fixed broken NHS search (old CSS selectors no longer work)
  - Uses direct URL patterns first (faster, more reliable)
  - Better content extraction (sections, truncation for small LLMs)
  - Removes navigation/footer noise before extracting content
  - Smarter fallback chain: direct URL → NHS search → alternatives
"""

import json
import asyncio
import logging
from typing import Any

import httpx
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp.nhs")

# --- NHS Data Fetchers ---

NHS_BASE_URL = "https://www.nhs.uk"
REQUEST_TIMEOUT = 15
USER_AGENT = "CareAI-Engine/1.0 (UK Medical Knowledge MCP Server)"

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/json",
}


def _extract_page_content(html: str, max_chars: int = 4000) -> dict:
    """
    Extract structured content from an NHS page.
    Optimised for small LLMs: focused sections, controlled length.
    Removes all navigation, footer, cookie banners etc.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove noise — navigation, footer, scripts, cookie banners
    for tag in soup.find_all(["nav", "footer", "script", "style", "noscript"]):
        tag.decompose()
    for cls in ["nhsuk-header", "nhsuk-footer", "nhsuk-cookie-banner",
                "nhsuk-breadcrumb", "nhsuk-action-link", "nhsuk-review-date",
                "nhsuk-related-nav", "nhsuk-pagination"]:
        for el in soup.find_all(class_=cls):
            el.decompose()

    main = soup.find("main") or soup.find("article") or soup.find("body")
    if not main:
        return {"text": "", "sections": []}

    sections = []
    current_section = {"heading": "Overview", "content": []}

    for el in main.find_all(["p", "li", "h2", "h3"]):
        text = el.get_text(strip=True)
        if not text or len(text) < 5:
            continue

        if el.name in ("h2", "h3"):
            if current_section["content"]:
                sections.append(current_section)
            current_section = {"heading": text, "content": []}
        else:
            current_section["content"].append(text)

    if current_section["content"]:
        sections.append(current_section)

    # Build text — truncate to fit small model context window
    full_text = ""
    for s in sections:
        section_text = f"\n## {s['heading']}\n" + "\n".join(s["content"])
        if len(full_text) + len(section_text) > max_chars:
            remaining = max_chars - len(full_text)
            if remaining > 100:
                full_text += section_text[:remaining] + "\n[...]"
            break
        full_text += section_text

    return {"text": full_text.strip(), "sections": sections}


async def fetch_nhs_page(path: str, max_chars: int = 4000) -> dict | None:
    """Fetch and parse a single NHS page."""
    url = f"{NHS_BASE_URL}{path}" if path.startswith("/") else path
    try:
        async with httpx.AsyncClient(
                timeout=REQUEST_TIMEOUT,
                headers=HEADERS,
                follow_redirects=True,
        ) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                content = _extract_page_content(resp.text, max_chars=max_chars)
                if content["text"]:
                    return {
                        "url": str(resp.url),
                        "status": "found",
                        **content,
                    }
                return {"url": str(resp.url), "status": "empty", "text": "", "sections": []}
            elif resp.status_code == 404:
                return {"url": url, "status": "not_found", "text": "", "sections": []}
            else:
                return {"url": url, "status": f"error_{resp.status_code}", "text": "", "sections": []}
    except httpx.TimeoutException:
        return {"url": url, "status": "timeout", "text": "", "sections": []}
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return {"url": url, "status": f"error: {str(e)[:100]}", "text": "", "sections": []}


async def search_nhs_site(query: str) -> list[dict]:
    """
    Search NHS website. Uses multiple CSS selectors for resilience
    against NHS redesigns.
    """
    try:
        async with httpx.AsyncClient(
                timeout=10,
                headers=HEADERS,
                follow_redirects=True,
        ) as client:
            resp = await client.get(
                f"{NHS_BASE_URL}/search/results",
                params={"q": query},
            )
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            results = []
            seen_urls = set()

            # Try multiple selectors — NHS changes these periodically
            selectors = [
                "a.nhsuk-link--no-visited-state",
                ".nhsuk-list-panel__item a",
                ".results__item a",
                ".nhsuk-list li a",
                "main a[href*='/medicines/']",
                "main a[href*='/conditions/']",
            ]

            for selector in selectors:
                for link in soup.select(selector):
                    href = link.get("href", "")
                    title = link.get_text(strip=True)
                    if not title or not href:
                        continue
                    if "/medicines/" in href or "/conditions/" in href:
                        full_url = href if href.startswith("http") else f"{NHS_BASE_URL}{href}"
                        if full_url not in seen_urls:
                            seen_urls.add(full_url)
                            results.append({
                                "title": title,
                                "url": full_url,
                                "path": href if href.startswith("/") else href.replace(NHS_BASE_URL, ""),
                            })

            return results[:8]

    except Exception as e:
        logger.warning(f"NHS search failed: {e}")
        return []


# --- MCP Tool Definitions ---

TOOLS = [
    {
        "name": "get_medicine_info",
        "description": (
            "Get detailed NHS information about a specific medicine. "
            "Fetches LIVE data from NHS.uk including: what it's for, dosage, "
            "side effects, interactions, and warnings. "
            "Use the medicine's common name (e.g., 'amlodipine', 'paracetamol')."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "medicine_name": {
                    "type": "string",
                    "description": "Common name of the medicine (e.g., 'amlodipine', 'ibuprofen')",
                },
                "section": {
                    "type": "string",
                    "description": "Optional specific section (e.g., 'side-effects', 'dosage', 'about')",
                    "default": "",
                },
            },
            "required": ["medicine_name"],
        },
    },
    {
        "name": "get_condition_info",
        "description": (
            "Get detailed NHS information about a medical condition. "
            "Fetches LIVE data from NHS.uk including: symptoms, causes, "
            "treatment, and prevention. "
            "Use the condition slug (e.g., 'type-2-diabetes', 'high-blood-pressure-hypertension')."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "condition_name": {
                    "type": "string",
                    "description": "Condition name or slug (e.g., 'dementia', 'type-2-diabetes')",
                },
            },
            "required": ["condition_name"],
        },
    },
    {
        "name": "search_nhs",
        "description": (
            "Search the NHS website for medical information. "
            "Use this when you don't know the exact medicine or condition name, "
            "or when the query is broad (e.g., 'pain relief options', 'blood pressure medications')."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'blood pressure medication', 'chest pain')",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_bnf_info",
        "description": (
            "Search the OpenPrescribing/BNF database for UK prescribing data. "
            "Useful for medication codes, prescribing patterns, and formulary information."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Medicine or BNF category to search for",
                },
            },
            "required": ["query"],
        },
    },
]


# --- MCP Tool Handlers ---

async def handle_tool_call(tool_name: str, arguments: dict) -> dict:
    """Route tool calls to the appropriate handler."""

    if tool_name == "get_medicine_info":
        medicine = arguments["medicine_name"].lower().strip().replace(" ", "-")
        section = arguments.get("section", "")

        # Try section-specific page first
        if section:
            section_slug = section.lower().strip().replace(" ", "-")
            result = await fetch_nhs_page(f"/medicines/{medicine}/{section_slug}/")
            if result and result["status"] == "found":
                return {
                    "success": True,
                    "medicine": arguments["medicine_name"],
                    "source": "NHS Medicines",
                    "url": result["url"],
                    "content": result["text"],
                    "sections": result["sections"],
                }

        # Try medicine hub page
        result = await fetch_nhs_page(f"/medicines/{medicine}/")
        if result and result["status"] == "found":
            return {
                "success": True,
                "medicine": arguments["medicine_name"],
                "source": "NHS Medicines",
                "url": result["url"],
                "content": result["text"],
                "sections": result["sections"],
            }

        # Try without hyphens
        medicine_alt = arguments["medicine_name"].lower().strip()
        if medicine_alt != medicine:
            result = await fetch_nhs_page(f"/medicines/{medicine_alt}/")
            if result and result["status"] == "found":
                return {
                    "success": True,
                    "medicine": arguments["medicine_name"],
                    "source": "NHS Medicines",
                    "url": result["url"],
                    "content": result["text"],
                    "sections": result["sections"],
                }

        return {
            "success": False,
            "medicine": arguments["medicine_name"],
            "message": f"Medicine '{arguments['medicine_name']}' not found on NHS.uk.",
        }

    elif tool_name == "get_condition_info":
        condition = arguments["condition_name"].lower().strip().replace(" ", "-")

        result = await fetch_nhs_page(f"/conditions/{condition}/")
        if result and result["status"] == "found":
            return {
                "success": True,
                "condition": arguments["condition_name"],
                "source": "NHS Conditions",
                "url": result["url"],
                "content": result["text"],
                "sections": result["sections"],
            }

        # Try alternative slugs
        for alt in [
            condition.replace("-", ""),
            condition + "s",
            condition.rstrip("s"),
        ]:
            if alt != condition:
                result = await fetch_nhs_page(f"/conditions/{alt}/")
                if result and result["status"] == "found":
                    return {
                        "success": True,
                        "condition": arguments["condition_name"],
                        "source": "NHS Conditions",
                        "url": result["url"],
                        "content": result["text"],
                        "sections": result["sections"],
                    }

        return {
            "success": False,
            "condition": arguments["condition_name"],
            "message": f"Condition '{arguments['condition_name']}' not found.",
        }

    elif tool_name == "search_nhs":
        query = arguments["query"]
        slug = query.lower().strip().replace(" ", "-")
        results = []

        # Strategy 1: Try direct URLs (fastest, most reliable)
        med_result = await fetch_nhs_page(f"/medicines/{slug}/")
        if med_result and med_result["status"] == "found":
            results.append({
                "title": f"{query.title()} (Medicine)",
                "url": med_result["url"],
                "type": "medicine",
                "content": med_result["text"],
            })

        cond_result = await fetch_nhs_page(f"/conditions/{slug}/")
        if cond_result and cond_result["status"] == "found":
            results.append({
                "title": f"{query.title()} (Condition)",
                "url": cond_result["url"],
                "type": "condition",
                "content": cond_result["text"],
            })

        if results:
            return {"success": True, "query": query, "results": results}

        # Strategy 2: NHS site search
        search_results = await search_nhs_site(query)
        if search_results:
            detailed_results = []
            for sr in search_results[:3]:
                path = sr["path"] if sr["path"].startswith("/") else sr["url"].replace(NHS_BASE_URL, "")
                page = await fetch_nhs_page(path)
                if page and page["status"] == "found":
                    detailed_results.append({
                        "title": sr["title"],
                        "url": sr["url"],
                        "content": page["text"],
                    })

            if detailed_results:
                return {
                    "success": True,
                    "query": query,
                    "results": detailed_results,
                    "total_found": len(search_results),
                }

        return {"success": False, "query": query, "results": [], "message": "No results found"}

    elif tool_name == "get_bnf_info":
        query = arguments["query"].lower()
        try:
            async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
                resp = await client.get(
                    "https://openprescribing.net/api/1.0/bnf_code/",
                    params={"q": query, "format": "json"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = [
                        {"code": item.get("id", ""), "name": item.get("name", "")}
                        for item in data[:20]
                    ]
                    return {"success": True, "query": query, "results": results, "source": "OpenPrescribing/BNF"}
        except Exception as e:
            logger.error(f"BNF search error: {e}")

        return {"success": False, "query": query, "message": "BNF data unavailable"}

    else:
        return {"success": False, "message": f"Unknown tool: {tool_name}"}


# --- MCP Protocol (JSON-RPC over stdio) ---

async def handle_jsonrpc(request: dict) -> dict:
    """Handle a JSON-RPC 2.0 request (MCP protocol)."""
    method = request.get("method", "")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "careai-nhs-server", "version": "3.0.0"},
            },
        }
    elif method == "notifications/initialized":
        return None
    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    elif method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        logger.info(f"Tool call: {tool_name} with args: {arguments}")
        result = await handle_tool_call(tool_name, arguments)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                "isError": not result.get("success", False),
            },
        }
    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }


async def run_stdio_server():
    """Run the MCP server over stdin/stdout (standard MCP transport)."""
    import sys
    logger.info("NHS MCP Server starting (stdio mode)...")
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
    writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
        asyncio.streams.FlowControlMixin, sys.stdout
    )
    writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, asyncio.get_event_loop())
    while True:
        try:
            line = await reader.readline()
            if not line:
                break
            request = json.loads(line.decode().strip())
            response = await handle_jsonrpc(request)
            if response:
                writer.write((json.dumps(response) + "\n").encode())
                await writer.drain()
        except json.JSONDecodeError:
            continue
        except Exception as e:
            logger.error(f"Server error: {e}")

if __name__ == "__main__":
    asyncio.run(run_stdio_server())
