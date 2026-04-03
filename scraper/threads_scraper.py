"""
Threads public profile scraper.

Scrapes reposts from a public Threads account without requiring
API credentials. Uses Threads' internal GraphQL API.

NOTE: Threads internal API endpoints (doc_ids) may change.
If this breaks, check: https://github.com/junhoyeo/threads-api
for the latest doc_ids.
"""

import json
import re
import time
import logging
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)


class ThreadsScraper:
    GRAPHQL_URL = "https://www.threads.net/api/graphql"
    APP_ID = "238260118697367"

    def __init__(self, username: str):
        self.username = username.lstrip("@")
        self.session = requests.Session()
        self._lsd: str | None = None
        self._user_id: str | None = None

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _load_page(self) -> str:
        """Fetch the public profile page and extract session tokens."""
        resp = self.session.get(
            f"https://www.threads.net/@{self.username}",
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/121.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=20,
        )
        resp.raise_for_status()
        html = resp.text

        # Extract LSD CSRF token
        m = re.search(r'"LSD",\[\],\{"token":"([^"]+)"\}', html)
        self._lsd = m.group(1) if m else "AVqbxe3J_YA"
        logger.info("LSD token: %s", self._lsd)

        # Try to extract user_id from embedded page data
        uid_m = re.search(r'"user_id"\s*:\s*"?(\d+)"?', html)
        if uid_m:
            self._user_id = uid_m.group(1)
            logger.info("Extracted user_id from HTML: %s", self._user_id)
        else:
            # Try alternate pattern
            uid_m2 = re.search(r'"pk"\s*:\s*"?(\d+)"?', html)
            if uid_m2:
                self._user_id = uid_m2.group(1)
                logger.info("Extracted user_id (pk) from HTML: %s", self._user_id)

        # Update session headers for subsequent API calls
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/121.0.0.0 Safari/537.36"
                ),
                "X-FB-LSD": self._lsd,
                "X-IG-App-ID": self.APP_ID,
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://www.threads.net",
                "Referer": f"https://www.threads.net/@{self.username}",
            }
        )
        return html

    def _graphql(self, doc_id: str, variables: dict) -> dict:
        resp = self.session.post(
            self.GRAPHQL_URL,
            data={
                "lsd": self._lsd,
                "variables": json.dumps(variables),
                "doc_id": doc_id,
            },
            timeout=20,
        )
        logger.info("GraphQL %s status=%s body=%r", doc_id, resp.status_code, resp.text[:500])
        resp.raise_for_status()
        if not resp.text.strip():
            raise RuntimeError(
                f"Threads API returned empty response for doc_id={doc_id}. "
                "The doc_id may have changed or the request was blocked."
            )
        return resp.json()

    def _resolve_user_id(self) -> str:
        """Resolve username → numeric user ID via REST API."""
        resp = self.session.get(
            "https://www.threads.net/api/v1/users/web_profile_info/",
            params={"username": self.username},
            headers={
                "x-ig-app-id": self.APP_ID,
                "User-Agent": "Instagram 289.0.0.77.109 Android",
            },
            timeout=20,
        )
        resp.raise_for_status()
        try:
            data = resp.json()
            user_id = data["data"]["user"]["id"]
            return str(user_id)
        except (ValueError, KeyError, TypeError) as exc:
            raise RuntimeError(
                f"Could not resolve user ID for @{self.username}. "
                f"Response: {resp.text[:200]}"
            ) from exc

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def get_reposts(self, max_count: int = 50) -> list[dict]:
        """
        Return recent reposts from the user's Threads profile.

        A "repost" is any thread item whose original author
        differs from self.username.

        Each returned dict has the shape:
          {
            "threads_post_id": str,
            "original_author":  str,
            "original_content": str,
            "reposted_at":      str (ISO-8601),
          }
        """
        self._load_page()
        if not self._user_id:
            self._user_id = self._resolve_user_id()
        logger.info("Resolved @%s → user_id=%s", self.username, self._user_id)

        # Fetch the user's thread feed
        data = self._graphql(
            doc_id="7357891684304218",  # get_user_threads
            variables={
                "userID": self._user_id,
                "count": max_count,
                "__relay_internal__pv__BarcelonaIsLoggedInrelayprovider": False,
            },
        )

        threads: list = (
            data.get("data", {})
            .get("mediaData", {})
            .get("threads", [])
        )

        reposts = []
        for thread in threads:
            for item in thread.get("thread_items", []):
                post = item.get("post", {})
                author = post.get("user", {}).get("username", "")

                if author.lower() == self.username.lower():
                    continue  # own post, not a repost

                caption = post.get("caption") or {}
                text = caption.get("text", "").strip() if isinstance(caption, dict) else ""

                if not text:
                    continue  # skip reposts with no text

                taken_at = post.get("taken_at", 0)
                reposted_at = datetime.fromtimestamp(taken_at, tz=timezone.utc).isoformat()

                reposts.append(
                    {
                        "threads_post_id": str(post.get("pk", "")),
                        "original_author": author,
                        "original_content": text,
                        "reposted_at": reposted_at,
                    }
                )

                time.sleep(0.1)  # be polite

        logger.info("Found %d reposts for @%s", len(reposts), self.username)
        return reposts
