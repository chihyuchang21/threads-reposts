"""
Idea extractor: uses Claude to turn a repost into a structured idea
with category suggestion and extended thinking questions.
"""

import json
import logging
import os

import anthropic

logger = logging.getLogger(__name__)

# Haiku is used here intentionally — this runs daily on every new repost.
# Switch to claude-opus-4-6 if you want deeper extraction.
MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = """\
You are a personal knowledge curator. The user reposts content on Threads
to capture ideas that resonate with them.

Your job: given a repost, extract the core idea in 1-3 concise sentences,
suggest a category, and generate 2-3 thought-provoking follow-up questions
that help the user think deeper.

Respond ONLY with valid JSON in this exact shape:
{
  "idea": "<core idea in 1-3 sentences>",
  "category": "<one short category label, e.g. 設計思維 / Tech / 心理學 / 創業 / 生活哲學>",
  "extended_thoughts": [
    "<question 1>",
    "<question 2>",
    "<question 3>"
  ]
}
"""


def extract_idea(
    original_author: str,
    original_content: str,
    existing_categories: list[str] | None = None,
) -> dict:
    """
    Extract an idea from a repost.

    Args:
        original_author:    Threads username of the original poster.
        original_content:   Text content of the reposted thread.
        existing_categories: Categories already in the library, for
                             consistency (Claude will prefer these).

    Returns:
        {
            "content":           str,   # extracted idea
            "category":          str,
            "extended_thoughts": list[str],
        }
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    cat_hint = ""
    if existing_categories:
        cat_hint = (
            f"\n\nExisting categories in the library (prefer these if relevant): "
            + ", ".join(existing_categories)
        )

    user_msg = (
        f"Original author: @{original_author}\n\n"
        f"Repost content:\n{original_content}"
        + cat_hint
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Claude returned non-JSON, using raw text as idea")
        parsed = {
            "idea": raw[:500],
            "category": "Uncategorized",
            "extended_thoughts": [],
        }

    return {
        "content": parsed.get("idea", ""),
        "category": parsed.get("category", "Uncategorized"),
        "extended_thoughts": parsed.get("extended_thoughts", []),
    }
