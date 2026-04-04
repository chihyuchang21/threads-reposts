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
from idea_extractor import extract_ideas_batch
from threads_scraper import ThreadsScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

THREADS_USERNAME = os.environ.get("THREADS_USERNAME", "hskkfuuennbx")


def run() -> None:
    logger.info("Starting scrape for @%s", THREADS_USERNAME)

    # 1. Check if this is the first run (empty DB)
    existing_ids = get_existing_post_ids()
    is_first_run = len(existing_ids) == 0

    if is_first_run:
        logger.info("First run detected — fetching full repost history")
        max_count, max_scrolls = 500, 40
    else:
        logger.info("Daily run — fetching recent reposts only")
        max_count, max_scrolls = 50, 4

    # 2. Fetch reposts from Threads
    scraper = ThreadsScraper(THREADS_USERNAME)
    try:
        reposts = scraper.get_reposts(max_count=max_count, max_scrolls=max_scrolls)
    except Exception as exc:
        logger.error("Scraping failed: %s", exc, exc_info=True)
        sys.exit(1)

    if not reposts:
        logger.info("No reposts found — done.")
        return

    # 3. Skip already-processed posts
    new_reposts = [r for r in reposts if r["threads_post_id"] not in existing_ids]
    logger.info("%d new repost(s) to process (skipping %d existing)",
                len(new_reposts), len(reposts) - len(new_reposts))

    if not new_reposts:
        logger.info("Nothing new — done.")
        return

    # 4. Extract ideas for all new reposts in a single API call
    existing_categories = get_existing_categories()
    logger.info("Extracting ideas for %d repost(s) in 1 API call…", len(new_reposts))

    try:
        ideas = extract_ideas_batch(new_reposts, existing_categories)
    except Exception as exc:
        logger.error("Batch idea extraction failed: %s", exc, exc_info=True)
        sys.exit(1)

    # 5. Save each repost + idea
    for repost, idea in zip(new_reposts, ideas):
        try:
            save_repost_and_idea(repost, idea)
            if idea["category"] and idea["category"] not in existing_categories:
                existing_categories.append(idea["category"])
        except Exception as exc:
            logger.error(
                "Failed to save repost %s: %s",
                repost["threads_post_id"],
                exc,
                exc_info=True,
            )

    logger.info("Done — processed %d new repost(s).", len(new_reposts))


if __name__ == "__main__":
    run()
