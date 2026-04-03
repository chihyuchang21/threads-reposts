"""
Entry point for the daily scrape job.
Run via GitHub Actions or locally:

    cd scraper
    pip install -r requirements.txt
    cp ../.env.example ../.env   # fill in your values
    python main.py
"""

import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from db import get_existing_post_ids, get_existing_categories, save_repost_and_idea
from idea_extractor import extract_idea
from threads_scraper import ThreadsScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

THREADS_USERNAME = os.environ.get("THREADS_USERNAME", "hskkfuuennbx")


def run() -> None:
    logger.info("Starting scrape for @%s", THREADS_USERNAME)

    # 1. Fetch reposts from Threads
    scraper = ThreadsScraper(THREADS_USERNAME)
    try:
        reposts = scraper.get_reposts(max_count=50)
    except Exception as exc:
        logger.error("Scraping failed: %s", exc, exc_info=True)
        sys.exit(1)

    if not reposts:
        logger.info("No reposts found — done.")
        return

    # 2. Skip already-processed posts
    existing_ids = get_existing_post_ids()
    new_reposts = [r for r in reposts if r["threads_post_id"] not in existing_ids]
    logger.info("%d new repost(s) to process (skipping %d existing)",
                len(new_reposts), len(reposts) - len(new_reposts))

    if not new_reposts:
        logger.info("Nothing new — done.")
        return

    # 3. Extract idea for each new repost
    existing_categories = get_existing_categories()

    for repost in new_reposts:
        try:
            logger.info(
                "Extracting idea from @%s repost: %.60s…",
                repost["original_author"],
                repost["original_content"],
            )
            idea = extract_idea(
                original_author=repost["original_author"],
                original_content=repost["original_content"],
                existing_categories=existing_categories,
            )
            save_repost_and_idea(repost, idea)

            # Keep category list fresh for next iteration
            if idea["category"] and idea["category"] not in existing_categories:
                existing_categories.append(idea["category"])

        except Exception as exc:
            logger.error(
                "Failed to process repost %s: %s",
                repost["threads_post_id"],
                exc,
                exc_info=True,
            )

    logger.info("Done — processed %d new repost(s).", len(new_reposts))


if __name__ == "__main__":
    run()
