# search_provider.py
# -*- coding: utf-8 -*-

import re
import time
import html
from functools import lru_cache
from urllib.parse import quote_plus, unquote, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize_url(url: str) -> str:
    if not url:
        return ""
    url = url.strip()

    # DuckDuckGo リダイレクト対策
    if "duckduckgo.com/l/?" in url:
        try:
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            uddg = qs.get("uddg", [""])[0]
            if uddg:
                url = unquote(uddg)
        except Exception:
            pass

    # Google/Bing系の余計な末尾除去
    url = re.sub(r"#.*$", "", url)
    url = re.sub(r"\?.*$", "", url)
    return url


def _is_valid_candidate_url(url: str) -> bool:
    if not url:
        return False

    ng = [
        "youtube.com",
        "facebook.com",
        "instagram.com",
        "x.com",
        "twitter.com",
        "tiktok.com",
        "ameblo.jp",
        "note.com",
        "wantedly.com",
        "jobmedley.com",
        "indeed.com",
        "en-gage.net",
        "townwork.net",
        "hatalike.jp",
        "jp.indeed.com",
        "google.com",
        "webcache.googleusercontent.com",
    ]
    if any(x in url for x in ng):
        return False

    return url.startswith("http://") or url.startswith("https://")


def _request_html(url: str, timeout: int = 8) -> str:
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.text


def _search_duckduckgo(query: str, max_results: int = 5):
    results = []
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

    try:
        html_text = _request_html(url, timeout=8)
        soup = BeautifulSoup(html_text, "html.parser")

        for a in soup.select("a.result__a"):
            href = a.get("href", "").strip()
            title = _clean_text(a.get_text(" ", strip=True))
            href = _normalize_url(href)

            if not _is_valid_candidate_url(href):
                continue

            parent = a.find_parent("div", class_="result")
            snippet = ""
            if parent:
                sn = parent.select_one(".result__snippet")
                if sn:
                    snippet = _clean_text(sn.get_text(" ", strip=True))

            results.append({
                "title": title,
                "url": href,
                "snippet": snippet,
                "provider": "duckduckgo",
            })

            if len(results) >= max_results:
                break
    except Exception:
        pass

    return results


def _search_bing(query: str, max_results: int = 5):
    results = []
    url = f"https://www.bing.com/search?q={quote_plus(query)}&setlang=ja-JP"

    try:
        html_text = _request_html(url, timeout=8)
        soup = BeautifulSoup(html_text, "html.parser")

        for li in soup.select("li.b_algo"):
            a = li.select_one("h2 a")
            if not a:
                continue

            href = _normalize_url(a.get("href", "").strip())
            title = _clean_text(a.get_text(" ", strip=True))
            snippet_el = li.select_one(".b_caption p")
            snippet = _clean_text(snippet_el.get_text(" ", strip=True)) if snippet_el else ""

            if not _is_valid_candidate_url(href):
                continue

            results.append({
                "title": title,
                "url": href,
                "snippet": snippet,
                "provider": "bing",
            })

            if len(results) >= max_results:
                break
    except Exception:
        pass

    return results


def search_web(query: str, max_results: int = 6, debug: bool = False):
    """
    軽量な複数検索プロバイダ集約。
    max_results は最終返却件数。
    """
    collected = []
    seen = set()

    providers = [
        _search_duckduckgo,
        _search_bing,
    ]

    for fn in providers:
        try:
            partial = fn(query, max_results=max_results)
            for row in partial:
                url = row.get("url", "")
                if not url or url in seen:
                    continue
                seen.add(url)
                collected.append(row)
                if len(collected) >= max_results:
                    return collected
        except Exception:
            continue

    return collected[:max_results]


@lru_cache(maxsize=128)
def fetch_page_text(url: str, timeout: int = 8, max_chars: int = 25000) -> str:
    """
    本文取得専用。
    大きすぎるHTMLでも最低限の本文に圧縮。
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()

        content_type = r.headers.get("Content-Type", "")
        if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
            return ""

        soup = BeautifulSoup(r.text, "html.parser")

        for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "aside"]):
            tag.decompose()

        text = soup.get_text("\n", strip=True)
        text = _clean_text(text)

        if len(text) > max_chars:
            text = text[:max_chars]

        return text
    except Exception:
        return ""


def get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""
