"""
Care AI Engine - MCP Client v3
Connects your medical agent to MCP tool servers (NHS, BNF, etc.).

v3 changes:
  - Smart question parsing: extracts medicine/condition names from natural language
  - Direct URL strategy first (skip broken search)
  - Better fallback chain
  - Limits context size for small LLMs
"""

import re
import time
from typing import Optional

from app.core.logging import get_logger
from app.mcp.servers.nhs_server import handle_tool_call, TOOLS
from app.services import cache_service

logger = get_logger("mcp.client")

# --- Common medical terms for smarter extraction ---

# Words that signal "the next words are a medicine name"
MEDICINE_SIGNALS = {
    "of", "for", "about", "called", "named", "taking", "prescribed",
    "medication", "medicine", "drug", "tablet", "capsule",
}

# Words that signal "this is about a condition/disease"
CONDITION_SIGNALS = {
    "manage", "treatment", "treat", "symptoms", "signs", "diagnosis",
    "condition", "disease", "disorder", "syndrome", "infection",
}

# Section keywords → NHS URL sections
SECTION_MAP = {
    "side effect": "side-effects",
    "side-effect": "side-effects",
    "adverse": "side-effects",
    "dosage": "how-and-when-to-take",
    "dose": "how-and-when-to-take",
    "how to take": "how-and-when-to-take",
    "how much": "how-and-when-to-take",
    "interaction": "taking-amlodipine-with-other-medicines-and-herbal-supplements",
    "who can": "who-can-and-cannot-take",
    "who cannot": "who-can-and-cannot-take",
    "pregnancy": "who-can-and-cannot-take",
    "breastfeed": "who-can-and-cannot-take",
}

# Stop words to ignore when extracting terms
STOP_WORDS = {
    "what", "are", "the", "is", "of", "for", "in", "a", "an", "and", "or",
    "to", "how", "should", "could", "would", "can", "do", "does", "my",
    "me", "i", "we", "our", "their", "this", "that", "it", "be", "been",
    "being", "have", "has", "had", "will", "shall", "may", "might",
    "with", "from", "about", "into", "through", "during", "before",
    "after", "above", "below", "between", "same", "different",
    "client", "patient", "person", "carer", "nurse", "elderly",
    "please", "tell", "explain", "describe", "help", "give",
    "recommended", "common", "most", "best", "worst",
}


def _extract_medical_terms(question: str) -> dict:
    """
    Parse a natural language question to extract:
      - medicine_name: if the question is about a specific medicine
      - condition_name: if the question is about a condition
      - section: if asking about a specific aspect (side effects, dosage, etc.)

    Examples:
      "What are the side effects of Amlodipine?" → medicine=amlodipine, section=side-effects
      "How should I manage type 2 diabetes?" → condition=type-2-diabetes
      "Signs of a UTI in elderly patients" → condition=urinary-tract-infections
    """
    q = question.lower().strip()

    result = {
        "medicine_name": None,
        "condition_name": None,
        "section": None,
        "search_query": question,  # Fallback: use whole question
    }

    # Detect section from question
    for pattern, section_slug in SECTION_MAP.items():
        if pattern in q:
            result["section"] = section_slug
            break

    # Pattern 1: "... of/for/about [TERM]" (most common pattern)
    # e.g., "side effects of Amlodipine", "dosage for paracetamol"
    match = re.search(
        r'(?:of|for|about|called|named|taking|prescribed)\s+([a-z][a-z0-9\s-]{2,30}?)(?:\?|$|\.|,|\s+(?:in|for|to|and|when|that|which|with))',
        q,
    )
    if match:
        term = match.group(1).strip().rstrip("s")  # Remove trailing 's'
        if term and term not in STOP_WORDS and len(term) > 2:
            # Guess: if it ends with common drug suffixes, it's a medicine
            drug_suffixes = ("pine", "pril", "olol", "statin", "mab", "nib",
                             "tide", "zole", "mycin", "cillin", "prazole",
                             "sartan", "gliptin", "flozin", "mol", "fen",
                             "codone", "morphine", "oxacin")
            if any(term.endswith(s) for s in drug_suffixes):
                result["medicine_name"] = term
            else:
                # Could be either — we'll try both
                result["medicine_name"] = term
                result["condition_name"] = term

    # Pattern 2: "manage/treat [CONDITION]"
    match = re.search(
        r'(?:manage|treat|treatment|symptoms|signs|diagnosis|prevent)\s+(?:a\s+|an\s+)?(?:client\s+with\s+|patient\s+with\s+)?([a-z][a-z0-9\s-]{2,40}?)(?:\?|$|\.|,)',
        q,
    )
    if match:
        term = match.group(1).strip()
        # Clean up trailing words
        for stop in ["in", "for", "to", "and", "when", "patient", "client", "elderly"]:
            term = re.sub(rf'\s+{stop}\s*$', '', term)
        if term and len(term) > 2:
            result["condition_name"] = term

    # Pattern 3: If nothing matched, extract the most "medical" looking words
    if not result["medicine_name"] and not result["condition_name"]:
        words = q.split()
        candidates = [w for w in words if w not in STOP_WORDS and len(w) > 3]

        # Try each candidate
        for word in candidates:
            drug_suffixes = ("pine", "pril", "olol", "statin", "mab", "mol",
                             "fen", "zole", "mycin", "cillin")
            if any(word.endswith(s) for s in drug_suffixes):
                result["medicine_name"] = word
                break

        # If still nothing, use the longest non-stop word as search query
        if candidates:
            result["search_query"] = " ".join(candidates[:4])

    # Normalise names for URLs
    if result["medicine_name"]:
        result["medicine_name"] = result["medicine_name"].strip().replace(" ", "-")
    if result["condition_name"]:
        result["condition_name"] = result["condition_name"].strip().replace(" ", "-")

    logger.info(f"Question parsed: medicine={result['medicine_name']}, "
                f"condition={result['condition_name']}, section={result['section']}")

    return result


class MCPClient:
    """MCP client that routes tool calls to registered servers."""

    def __init__(self):
        self._tool_registry: dict[str, dict] = {}
        self._register_nhs_tools()

    def _register_nhs_tools(self):
        for tool in TOOLS:
            self._tool_registry[tool["name"]] = {
                "description": tool["description"],
                "schema": tool["inputSchema"],
                "server": "nhs",
            }
        logger.info(f"Registered {len(TOOLS)} NHS MCP tools")

    @property
    def available_tools(self) -> list[dict]:
        return [
            {"name": name, "description": info["description"], "server": info["server"]}
            for name, info in self._tool_registry.items()
        ]

    @property
    def tool_descriptions_for_llm(self) -> str:
        lines = ["Available medical data tools:"]
        for name, info in self._tool_registry.items():
            lines.append(f"  - {name}: {info['description']}")
        return "\n".join(lines)

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call an MCP tool with caching."""
        if tool_name not in self._tool_registry:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}. Available: {list(self._tool_registry.keys())}",
            }

        start = time.monotonic()

        # Check cache
        cached = await cache_service.get_cached(tool_name, arguments)
        if cached is not None:
            duration_ms = (time.monotonic() - start) * 1000
            logger.info(f"MCP tool (CACHED): {tool_name}", extra={"tool": tool_name, "cached": True, "duration_ms": round(duration_ms, 1)})
            cached["_meta"] = {"tool": tool_name, "duration_ms": round(duration_ms, 1), "source": "cache"}
            return cached

        # Fetch live
        try:
            result = await handle_tool_call(tool_name, arguments)
            duration_ms = (time.monotonic() - start) * 1000
            logger.info(f"MCP tool (LIVE): {tool_name}", extra={"tool": tool_name, "cached": False, "success": result.get("success", False), "duration_ms": round(duration_ms, 1)})
            await cache_service.set_cached(tool_name, arguments, result)
            result["_meta"] = {"tool": tool_name, "duration_ms": round(duration_ms, 1), "source": "live"}
            return result
        except Exception as e:
            logger.error(f"MCP tool error: {tool_name} - {e}", exc_info=True)
            return {"success": False, "error": f"Tool execution failed: {str(e)[:200]}"}

    async def fetch_medical_context(
            self,
            question: str,
            strategy: str = "auto",
    ) -> dict:
        """
        High-level: Given a user question, fetch the right medical context.

        v3 strategy:
          1. Parse the question to extract medicine/condition names
          2. Try direct medicine/condition lookup (fast, reliable)
          3. Fall back to NHS search only if direct lookup fails
        """
        tools_used = []
        all_context = []
        sources = []

        if strategy == "auto":
            parsed = _extract_medical_terms(question)

            # Step 1: Try medicine lookup if a medicine name was detected
            if parsed["medicine_name"]:
                args = {"medicine_name": parsed["medicine_name"]}
                if parsed["section"]:
                    args["section"] = parsed["section"]

                med_result = await self.call_tool("get_medicine_info", args)
                tools_used.append("get_medicine_info")

                if med_result.get("success"):
                    all_context.append(med_result.get("content", ""))
                    sources.append({
                        "source": "NHS Medicines",
                        "name": med_result.get("medicine", parsed["medicine_name"]),
                        "url": med_result.get("url", ""),
                    })

            # Step 2: Try condition lookup if a condition name was detected
            if parsed["condition_name"] and not all_context:
                cond_result = await self.call_tool(
                    "get_condition_info",
                    {"condition_name": parsed["condition_name"]},
                )
                tools_used.append("get_condition_info")

                if cond_result.get("success"):
                    all_context.append(cond_result.get("content", ""))
                    sources.append({
                        "source": "NHS Conditions",
                        "name": cond_result.get("condition", parsed["condition_name"]),
                        "url": cond_result.get("url", ""),
                    })

            # Step 3: Fallback — search NHS
            if not all_context:
                search_result = await self.call_tool(
                    "search_nhs",
                    {"query": parsed["search_query"]},
                )
                tools_used.append("search_nhs")

                if search_result.get("success") and search_result.get("results"):
                    for r in search_result["results"][:2]:  # Max 2 results for context size
                        content = r.get("content", r.get("preview", ""))
                        if content:
                            all_context.append(content)
                            sources.append({
                                "source": "NHS",
                                "name": r.get("title", ""),
                                "url": r.get("url", ""),
                            })

        elif strategy == "medicine":
            result = await self.call_tool(
                "get_medicine_info", {"medicine_name": question}
            )
            tools_used.append("get_medicine_info")
            if result.get("success"):
                all_context.append(result.get("content", ""))
                sources.append({
                    "source": "NHS Medicines",
                    "name": result.get("medicine", ""),
                    "url": result.get("url", ""),
                })

        elif strategy == "condition":
            result = await self.call_tool(
                "get_condition_info", {"condition_name": question}
            )
            tools_used.append("get_condition_info")
            if result.get("success"):
                all_context.append(result.get("content", ""))
                sources.append({
                    "source": "NHS Conditions",
                    "name": result.get("condition", ""),
                    "url": result.get("url", ""),
                })

        elif strategy == "search":
            result = await self.call_tool("search_nhs", {"query": question})
            tools_used.append("search_nhs")
            if result.get("success"):
                for r in result.get("results", [])[:2]:
                    content = r.get("content", r.get("preview", ""))
                    if content:
                        all_context.append(content)
                        sources.append({
                            "source": "NHS",
                            "name": r.get("title", ""),
                            "url": r.get("url", ""),
                        })

        # Combine context — keep under 4000 chars for small LLM
        combined = "\n\n---\n\n".join(c for c in all_context if c)
        if len(combined) > 4000:
            combined = combined[:4000] + "\n\n[Content truncated for length]"

        return {
            "context": combined,
            "sources": sources,
            "tools_used": tools_used,
            "success": bool(combined.strip()),
        }


# Global singleton
mcp_client = MCPClient()
