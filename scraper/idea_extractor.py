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

You will receive a JSON array of reposts. For EACH item:
- Extract the core idea in 1-3 concise sentences IN ENGLISH (idea_en)
- Translate that same idea into Traditional Chinese (idea_zh)
- Suggest ONE short category label IN ENGLISH ONLY (e.g. Career, Psychology, Tech, Productivity, Gender, Relationships, Learning, Life Philosophy, AI Tools, Design)
- Generate 2-3 thought-provoking follow-up questions IN ENGLISH

Respond ONLY with a valid JSON array. Each element MUST include the original
"index" from the input so results can be matched back correctly:
[
  {
    "index": 0,
    "idea_en": "<core idea in English, 1-3 sentences>",
    "idea_zh": "<same idea in Traditional Chinese, 1-3 sentences>",
    "category": "<one short English category label>",
    "extended_thoughts": ["<question 1>", "<question 2>", "<question 3>"]
  },
  ...
]
"""

_FALLBACK = {
    "content": "",
    "content_zh": "",
    "category": "Uncategorized",
    "extended_thoughts": [],
}


def _parse_raw(raw: str) -> list[dict]:
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


BATCH_SIZE = 20  # max reposts per API call to stay within output token limit


def _extract_chunk(
    client: anthropic.Anthropic,
    chunk: list[dict],
    cat_hint: str,
) -> list[dict]:
    """Send one chunk of reposts to Claude and return parsed ideas."""
    payload = [
        {"index": i, "author": r["original_author"], "content": r["original_content"]}
        for i, r in enumerate(chunk)
    ]
    user_msg = json.dumps(payload, ensure_ascii=False) + cat_hint

    response = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = response.content[0].text.strip()

    try:
        parsed = _parse_raw(raw)
    except (json.JSONDecodeError, IndexError):
        logger.warning("Claude returned non-JSON for chunk of %d, using fallbacks", len(chunk))
        return [_FALLBACK.copy() for _ in chunk]

    # Build a lookup by index so we handle missing or reordered items safely
    by_index: dict[int, dict] = {}
    for item in parsed:
        if not isinstance(item, dict):
            continue
        idx = item.get("index")
        if isinstance(idx, int):
            by_index[idx] = item

    results = []
    for i in range(len(chunk)):
        item = by_index.get(i)
        if not item:
            results.append(_FALLBACK.copy())
            continue
        results.append({
            "content": item.get("idea_en", ""),
            "content_zh": item.get("idea_zh", ""),
            "category": item.get("category", "Uncategorized"),
            "extended_thoughts": item.get("extended_thoughts", []),
        })

    return results


def extract_ideas_batch(
    reposts: list[dict],
    existing_categories: Optional[list[str]] = None,
) -> list[dict]:
    """
    Extract ideas from reposts, chunked to stay within output token limits.

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

    chunks = [reposts[i:i + BATCH_SIZE] for i in range(0, len(reposts), BATCH_SIZE)]
    all_results: list[dict] = []

    for idx, chunk in enumerate(chunks):
        logger.info("Extracting ideas: chunk %d/%d (%d reposts)", idx + 1, len(chunks), len(chunk))
        all_results.extend(_extract_chunk(client, chunk, cat_hint))

    logger.info("Batch extracted %d ideas in %d API call(s)", len(all_results), len(chunks))
    return all_results
