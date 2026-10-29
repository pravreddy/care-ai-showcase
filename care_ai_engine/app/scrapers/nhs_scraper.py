"""
Care AI Engine - NHS Data Scraper (Production)
Configurable scraper with rate limiting, change detection, and proper error handling.
Run as a standalone script or scheduled job.

Usage:
    python -m app.scrapers.nhs_scraper --medicines --conditions
"""

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.services.knowledge_base import knowledge_base
from app.core.logging import setup_logging, get_logger

logger = get_logger("scraper.nhs")

# --- Configurable Data Sources ---

NHS_MEDICINES = [
    "amlodipine", "paracetamol", "aspirin", "ibuprofen", "metformin",
    "atorvastatin", "warfarin", "ramipril", "simvastatin", "omeprazole",
    "lisinopril", "bisoprolol", "furosemide", "clopidogrel", "levothyroxine",
    "prednisolone", "amoxicillin", "codeine", "diazepam", "morphine",
    "gabapentin", "pregabalin", "sertraline", "citalopram", "fluoxetine",
    "lansoprazole", "bendroflumethiazide", "doxycycline", "naproxen",
    "tramadol", "co-codamol", "methotrexate", "insulin",
]

NHS_CONDITIONS = [
    "high-blood-pressure-hypertension", "type-2-diabetes", "dementia",
    "parkinsons-disease", "arthritis", "asthma", "copd", "heart-failure",
    "stroke", "falls", "urinary-tract-infections-utis", "pneumonia",
    "depression", "anxiety", "insomnia", "constipation", "diarrhoea",
    "dehydration", "pressure-ulcers-pressure-sores", "sepsis",
    "chest-pain", "atrial-fibrillation", "dvt-deep-vein-thrombosis",
    "epilepsy", "multiple-sclerosis", "osteoporosis",
]


class NHSScraper:
    """Production-grade NHS content scraper."""

    def __init__(self):
        settings = get_settings()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": settings.nhs_user_agent,
            "Accept": "text/html,application/xhtml+xml",
        })
        self.data_dir = Path("data")
        self.request_delay = 2.0  # seconds between requests (be respectful)

    def _extract_page_content(self, html: str) -> str:
        """Extract meaningful text content from an NHS page."""
        soup = BeautifulSoup(html, "html.parser")
        main = soup.find("main")
        if not main:
            return ""

        text_parts = []
        for el in main.find_all(["p", "li", "h2", "h3"]):
            text = el.get_text(strip=True)
            if text and len(text) > 10:
                # Prefix headings for better RAG retrieval
                if el.name in ("h2", "h3"):
                    text = f"\n## {text}\n"
                text_parts.append(text)

        return "\n".join(text_parts)

    def _save_json(self, category: str, name: str, data: dict) -> Path:
        """Save scraped data as JSON."""
        out_dir = self.data_dir / category
        out_dir.mkdir(parents=True, exist_ok=True)

        filepath = out_dir / f"{name}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return filepath

    def scrape_medicines(self) -> dict:
        """Scrape all configured medicines from NHS website."""
        results = {"success": 0, "failed": 0, "skipped": 0, "errors": []}

        for med in NHS_MEDICINES:
            url = f"https://www.nhs.uk/medicines/{med}/"
            logger.info(f"Scraping medicine: {med}")

            try:
                resp = self.session.get(url, timeout=15)

                if resp.status_code == 200:
                    content = self._extract_page_content(resp.text)
                    if not content:
                        logger.warning(f"No content extracted for {med}")
                        results["skipped"] += 1
                        continue

                    data = {
                        "name": med.title(),
                        "slug": med,
                        "content": content,
                        "source": "NHS Medicines",
                        "url": url,
                        "type": "medicine",
                        "content_hash": hashlib.sha256(content.encode()).hexdigest(),
                        "char_count": len(content),
                    }

                    self._save_json("medicines", med, data)

                    # Also load directly into knowledge base
                    knowledge_base.add_document(
                        doc_id=f"medicine_{med}",
                        content=content,
                        source="NHS Medicines",
                        doc_type="medicine",
                        url=url,
                        name=med.title(),
                    )

                    results["success"] += 1
                    logger.info(f"  ✓ {med} ({len(content)} chars)")

                elif resp.status_code == 404:
                    logger.warning(f"  ✗ {med} not found (404)")
                    results["failed"] += 1
                else:
                    logger.error(f"  ✗ {med} HTTP {resp.status_code}")
                    results["failed"] += 1
                    results["errors"].append(f"{med}: HTTP {resp.status_code}")

            except requests.Timeout:
                logger.error(f"  ✗ {med} timed out")
                results["failed"] += 1
                results["errors"].append(f"{med}: timeout")
            except Exception as e:
                logger.error(f"  ✗ {med} error: {e}")
                results["failed"] += 1
                results["errors"].append(f"{med}: {str(e)[:100]}")

            time.sleep(self.request_delay)

        return results

    def scrape_conditions(self) -> dict:
        """Scrape all configured conditions from NHS website."""
        results = {"success": 0, "failed": 0, "skipped": 0, "errors": []}

        for condition in NHS_CONDITIONS:
            url = f"https://www.nhs.uk/conditions/{condition}/"
            logger.info(f"Scraping condition: {condition}")

            try:
                resp = self.session.get(url, timeout=15)

                if resp.status_code == 200:
                    content = self._extract_page_content(resp.text)
                    if not content:
                        logger.warning(f"No content extracted for {condition}")
                        results["skipped"] += 1
                        continue

                    name = condition.replace("-", " ").title()
                    data = {
                        "name": name,
                        "slug": condition,
                        "content": content,
                        "source": "NHS Conditions",
                        "url": url,
                        "type": "condition",
                        "content_hash": hashlib.sha256(content.encode()).hexdigest(),
                        "char_count": len(content),
                    }

                    self._save_json("conditions", condition, data)

                    knowledge_base.add_document(
                        doc_id=f"condition_{condition}",
                        content=content,
                        source="NHS Conditions",
                        doc_type="condition",
                        url=url,
                        name=name,
                    )

                    results["success"] += 1
                    logger.info(f"  ✓ {name} ({len(content)} chars)")

                elif resp.status_code == 404:
                    logger.warning(f"  ✗ {condition} not found (404)")
                    results["failed"] += 1
                else:
                    logger.error(f"  ✗ {condition} HTTP {resp.status_code}")
                    results["failed"] += 1

            except Exception as e:
                logger.error(f"  ✗ {condition} error: {e}")
                results["failed"] += 1
                results["errors"].append(f"{condition}: {str(e)[:100]}")

            time.sleep(self.request_delay)

        return results


def main():
    parser = argparse.ArgumentParser(description="NHS Data Scraper")
    parser.add_argument("--medicines", action="store_true", help="Scrape medicines")
    parser.add_argument("--conditions", action="store_true", help="Scrape conditions")
    parser.add_argument("--all", action="store_true", help="Scrape everything")
    args = parser.parse_args()

    setup_logging()
    knowledge_base.init()

    scraper = NHSScraper()

    if args.all or args.medicines:
        logger.info("=== Scraping NHS Medicines ===")
        med_results = scraper.scrape_medicines()
        logger.info(f"Medicines: {med_results['success']} success, {med_results['failed']} failed")

    if args.all or args.conditions:
        logger.info("=== Scraping NHS Conditions ===")
        cond_results = scraper.scrape_conditions()
        logger.info(f"Conditions: {cond_results['success']} success, {cond_results['failed']} failed")

    stats = knowledge_base.get_stats()
    logger.info(f"Knowledge base total: {stats['total_documents']} documents")


if __name__ == "__main__":
    main()
