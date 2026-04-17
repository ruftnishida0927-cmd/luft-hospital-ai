from __future__ import annotations

import re
from collections import deque
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .classify import classify_url, infer_source_type
from .config import KNOWN_PATH_SEEDS, MAX_EXTERNAL_PAGES, MAX_LINKS_PER_PAGE, MAX_PAGES
from .http import Fetcher
from .models import Page
from .utils import domain, same_domain, strip_fragment, to_abs, unique_keep_order


def crawl_site(start_url: str):
    fetcher = Fetcher()
    seen = set()
    pages = []
    queue = deque([(strip_fragment(start_url), 0, "basic", "official")])
    root_domain = domain(start_url)

    for seed in KNOWN_PATH_SEEDS:
        queue.append((strip_fragment(start_url.rstrip("/") + seed), 1, classify_url(seed), "official"))

    external_seen = 0

    while queue and len(pages) < MAX_PAGES + MAX_EXTERNAL_PAGES:
        url, depth, category, source_type = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        try:
            final_url, content_type, title, status_code, text, html = fetcher.fetch_html(url)
        except Exception:
            continue

        page = Page(
            url=url,
            final_url=final_url,
            domain=domain(final_url),
            category=category if category != "unknown" else classify_url(final_url, title=title),
            title=title,
            text=text,
            html=html,
            content_type=content_type,
            status_code=status_code,
            fetched_at=fetcher.timestamp(),
            depth=depth,
            source_type=source_type,
        )
        pages.append(page)

        if "html" not in content_type.lower() and "xml" not in content_type.lower() and not final_url.endswith("/"):
            continue

        soup = BeautifulSoup(html, "lxml")
        links = []
        for a in soup.find_all("a", href=True)[:MAX_LINKS_PER_PAGE]:
            href = a.get("href", "")
            abs_url = to_abs(final_url, href)
            anchor = a.get_text(" ", strip=True)
            if not abs_url.startswith("http"):
                continue
            links.append((abs_url, anchor))
        page.anchors = [f"{anchor} -> {u}" for u, anchor in links[:20]]

        for abs_url, anchor in links:
            cat = classify_url(abs_url, anchor)
            st = infer_source_type(abs_url, cat)
            if same_domain(final_url, abs_url):
                path = urlparse(abs_url).path.lower()
                if any(skip in path for skip in [".jpg", ".png", ".gif", ".svg", ".css", ".js", ".ico"]):
                    continue
                if len(pages) + len(queue) < MAX_PAGES:
                    queue.append((abs_url, depth + 1, cat, "official"))
            else:
                if external_seen >= MAX_EXTERNAL_PAGES:
                    continue
                if st in {"public", "recruit", "group"}:
                    external_seen += 1
                    queue.append((abs_url, depth + 1, cat if cat != "unknown" else st, st))
    return pages
