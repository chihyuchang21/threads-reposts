"""
Threads profile scraper using Playwright with authenticated session.

Requires THREADS_SESSION_ID environment variable (the `sessionid` cookie
from a logged-in Threads/Instagram browser session).

Security notes:
- sessionid is stored as a GitHub secret (encrypted, never in logs)
- Only the sessionid cookie is needed — no password involved
- Expires after ~90 days; rotate by logging in again and updating the secret
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


class ThreadsScraper:
    def __init__(self, username: str, user_id: Optional[str] = None):
        self.username = username.lstrip("@")

    def get_reposts(self, max_count: int = 50) -> list[dict]:
        """
        Return recent reposts from the user's Threads profile.

        Requires THREADS_SESSION_ID env var (the sessionid cookie value).

        Each returned dict:
          {
            "threads_post_id": str,
            "original_author":  str,
            "original_content": str,
            "reposted_at":      str (ISO-8601),
          }
        """
        session_id = os.environ.get("THREADS_SESSION_ID")
        if not session_id:
            raise RuntimeError(
                "THREADS_SESSION_ID environment variable is required. "
                "Set it to the value of the 'sessionid' cookie from a logged-in Threads session."
            )

        captured: list[dict] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/121.0.0.0 Safari/537.36"
                )
            )

            # Inject session cookie — never logged
            context.add_cookies([
                {
                    "name": "sessionid",
                    "value": session_id,
                    "domain": ".threads.com",
                    "path": "/",
                    "httpOnly": True,
                    "secure": True,
                },
                {
                    "name": "sessionid",
                    "value": session_id,
                    "domain": ".instagram.com",
                    "path": "/",
                    "httpOnly": True,
                    "secure": True,
                },
            ])

            page = context.new_page()

            def handle_response(response):
                if "graphql" in response.url and response.status == 200:
                    try:
                        body = response.json()
                        threads = (
                            body.get("data", {})
                            .get("mediaData", {})
                            .get("threads", [])
                        )
                        if threads:
                            logger.info("Captured %d threads from GraphQL", len(threads))
                            captured.extend(threads)
                    except Exception:
                        pass

            page.on("response", handle_response)

            logger.info("Loading reposts page for @%s", self.username)
            page.goto(
                f"https://www.threads.com/@{self.username}/reposts",
                wait_until="networkidle",
                timeout=30000,
            )
            page.wait_for_timeout(3000)

            # Scroll down to trigger lazy-loading of reposts
            for _ in range(5):
                page.evaluate("window.scrollBy(0, 1200)")
                page.wait_for_timeout(1500)

            body_text = page.locator("body").inner_text()
            logger.info("Page preview: %s", body_text[:300].replace("\n", " "))
            logger.info("Logged in: %s", "Log in" not in body_text)

            # If GraphQL didn't fire, fall back to body text parsing
            if not captured:
                logger.info("No GraphQL data intercepted, trying body text parse")
                reposts = self._parse_body_text(body_text)
                browser.close()
                return reposts[:max_count]

            browser.close()

        reposts = []
        for thread in captured:
            for item in thread.get("thread_items", []):
                post = item.get("post", {})
                author = post.get("user", {}).get("username", "")

                if author.lower() == self.username.lower():
                    continue

                caption = post.get("caption") or {}
                text = caption.get("text", "").strip() if isinstance(caption, dict) else ""

                if not text:
                    continue

                taken_at = post.get("taken_at", 0)
                reposted_at = datetime.fromtimestamp(taken_at, tz=timezone.utc).isoformat()

                reposts.append({
                    "threads_post_id": str(post.get("pk", "")),
                    "original_author": author,
                    "original_content": text,
                    "reposted_at": reposted_at,
                })

        logger.info("Found %d reposts for @%s", len(reposts), self.username)
        return reposts[:max_count]

    def _parse_body_text(self, body_text: str) -> list[dict]:
        """
        Fallback: parse reposts from the page's inner_text().

        Threads renders post text as lines. Each post block looks like:
            username
            · Xh  (or Xm, Xd)
            post content...
            (optional: N replies, N reposts, N likes)

        We split on the time marker pattern and extract the content.
        """
        import re

        reposts = []
        seen = set()
        now = datetime.now(tz=timezone.utc).isoformat()

        # Split on lines and look for blocks: username → time → content
        lines = [l.strip() for l in body_text.splitlines() if l.strip()]

        # Time pattern: "· 5m", "· 2h", "· 3d", "56m", "2h", "3d"
        time_re = re.compile(r'^·?\s*\d+[smhdw]$')

        i = 0
        while i < len(lines):
            # Look for a time marker
            if time_re.match(lines[i]):
                # Author is the line before the time marker
                author = lines[i - 1] if i > 0 else "unknown"
                # Content starts after the time marker
                content_lines = []
                j = i + 1
                while j < len(lines):
                    # Stop at next time marker (next post)
                    if time_re.match(lines[j]):
                        break
                    # Stop at engagement metrics
                    if re.match(r'^\d+ (replies?|reposts?|likes?|quotes?)$', lines[j]):
                        j += 1
                        continue
                    content_lines.append(lines[j])
                    j += 1

                text = " ".join(content_lines).strip()
                if (
                    len(text) > 20
                    and text not in seen
                    and author.lower() != self.username.lower()
                ):
                    seen.add(text)
                    reposts.append({
                        "threads_post_id": str(abs(hash(text))),
                        "original_author": author,
                        "original_content": text,
                        "reposted_at": now,
                    })
                i = j
            else:
                i += 1

        logger.info("Body text parse found %d reposts", len(reposts))
        return reposts
