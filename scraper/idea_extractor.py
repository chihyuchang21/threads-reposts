"""
Idea extractor: uses Claude to turn reposts into structured ideas
with category suggestions and extended thinking questions.

All reposts are processed in a single API call to minimise cost.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)

# Haiku is used here intentionally — this runs daily on every new repost.
MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = """\
You are a personal knowledge curator. The user reposts content on Threads
to capture ideas that resonate with them.

You will receive a JSON array of reposts. For EACH item, extract the core idea
in 1-3 concise sentences, suggest a category, and generate 2-3 thought-provoking
follow-up questions that help the user think deeper.

Respond ONLY with a valid JSON array where each element corresponds to the input
at the same index, in this exact shape:
[
  {
    "idea": "<core idea in 1-3 sentences>",
    "category": "<one short category label, e.g. 設計思維 / Tech / 心理學 / 創業 / 生活哲學>",
    "extended_thoughts": ["<question 1>", "<question 2>", "<question 3>"]
  },
  ...
]
"""

_FALLBACK = {
    "content": "",
    "category": "Uncategorized",
    "extended_thoughts": [],
}


def _parse_raw(raw: str) -> list[dict]:
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def extract_ideas_batch(
    reposts: list[dict],
    existing_categories: Optional[list[str]] = None,
) -> list[dict]:
    """
    Extract ideas from multiple reposts in a single API call.

    Args:
        reposts: list of dicts with keys original_author, original_content.
        existing_categories: categories already in the library (for consistency).

    Returns:
        list of dicts with keys content, category, extended_thoughts.
        Same length as reposts; failed items get a fallback entry.
    """
    if not reposts:
        return []

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    cat_hint = ""
    if existing_categories:
        cat_hint = (
            "\n\nExisting categories in the library (prefer these if relevant): "
            + ", ".join(existing_categories)
        )

    payload = [
        {"index": i, "author": r["original_author"], "content": r["original_content"]}
        for i, r in enumerate(reposts)
    ]
    user_msg = json.dumps(payload, ensure_ascii=False) + cat_hint

    # Scale max_tokens with batch size: ~400 tokens output per repost
    max_tokens = min(max(1024, len(reposts) * 400), 8192)

    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = response.content[0].text.strip()

    try:
        parsed = _parse_raw(raw)
    except (json.JSONDecodeError, IndexError):
        logger.warning("Claude returned non-JSON for batch, falling back to empty ideas")
        return [_FALLBACK.copy() for _ in reposts]

    results = []
    for i, item in enumerate(parsed):
        if not isinstance(item, dict):
            results.append(_FALLBACK.copy())
            continue
        results.append({
            "content": item.get("idea", ""),
            "category": item.get("category", "Uncategorized"),
            "extended_thoughts": item.get("extended_thoughts", []),
        })

    # Pad if Claude returned fewer items than expected
    while len(results) < len(reposts):
        results.append(_FALLBACK.copy())

    logger.info("Batch extracted %d ideas in 1 API call", len(results))
    return results
