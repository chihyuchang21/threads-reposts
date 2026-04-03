"""Supabase database operations."""

import logging
import os

from supabase import create_client, Client

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_KEY"],
        )
    return _client


def get_existing_post_ids() -> set[str]:
    """Return all threads_post_ids already in the DB."""
    res = get_client().table("reposts").select("threads_post_id").execute()
    return {row["threads_post_id"] for row in res.data}


def get_existing_categories() -> list[str]:
    """Return distinct category names from the ideas table."""
    res = (
        get_client()
        .table("ideas")
        .select("category")
        .not_.is_("category", "null")
        .execute()
    )
    seen = set()
    cats = []
    for row in res.data:
        c = row["category"]
        if c and c not in seen:
            seen.add(c)
            cats.append(c)
    return cats


def save_repost_and_idea(
    repost: dict,
    idea: dict,
) -> None:
    """
    Insert a repost and its extracted idea in one transaction.

    repost shape:
        threads_post_id, original_author, original_content, reposted_at

    idea shape:
        content, category, extended_thoughts (list)
    """
    db = get_client()

    # Upsert repost (ignore duplicates)
    res = (
        db.table("reposts")
        .upsert(repost, on_conflict="threads_post_id")
        .execute()
    )
    repost_id = res.data[0]["id"]

    # Insert idea
    db.table("ideas").insert(
        {
            "repost_id": repost_id,
            "content": idea["content"],
            "category": idea["category"],
            "extended_thoughts": idea["extended_thoughts"],
            "status": "pending",
        }
    ).execute()

    logger.info(
        "Saved repost %s → idea [%s]",
        repost["threads_post_id"],
        idea["category"],
    )
