# search_provider.py
# -*- coding: utf-8 -*-

import re
import html
from urllib.parse import urlparse, urljoin, urldefrag

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


def get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def normalize_url(url: str, base_url: str = "") -> str:
    if not url:
        return ""

    if base_url:
        url = urljoin(base_url, url)

    url, _ = urldefrag(url)
    url = url.strip()

    # 明らかに不要なスキーム除外
    if url.startswith("mailto:") or url.startswith("tel:") or url.startswith("javascript:"):
        return ""

    return url


def is_http_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


def fetch_page_html(url: str, timeout: int = 15) -> tuple[str, str]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()

        content_type = r.headers.get("Content-Type", "")
        if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
            return "", f"HTML以外のContent-Typeです: {content_type}"

        return r.text, ""
    except Exception as e:
        return "", str(e)


def html_to_text(html_text: str, max_chars: int = 50000) -> str:
    if not html_text:
        return ""

    soup = BeautifulSoup(html_text, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "aside"]):
        tag.decompose()

    text = soup.get_text("\n", strip=True)
    text = html.unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    if len(text) > max_chars:
        text = text[:max_chars]

    return text


def fetch_page_text(url: str, timeout: int = 15, max_chars: int = 50000) -> str:
    html_text, err = fetch_page_html(url, timeout=timeout)
    if err:
        return ""
    return html_to_text(html_text, max_chars=max_chars)


def extract_links(url: str, html_text: str, same_domain_only: bool = False) -> list[dict]:
    if not html_text:
        return []

    base_domain = get_domain(url)
    soup = BeautifulSoup(html_text, "html.parser")

    rows = []
    seen = set()

    for a in soup.select("a[href]"):
        href = normalize_url(a.get("href", ""), base_url=url)
        if not href or not is_http_url(href):
            continue

        if same_domain_only and get_domain(href) != base_domain:
            continue

        if href in seen:
            continue
        seen.add(href)

        text = a.get_text(" ", strip=True)
        title = a.get("title", "").strip()

        rows.append({
            "url": href,
            "text": text,
            "title": title,
        })

    return rows
