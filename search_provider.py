# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, unquote


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive"
}


def fetch(url, method="GET", data=None):
    try:
        if method == "POST":
            return requests.post(
                url,
                headers=HEADERS,
                data=data,
                timeout=10
            )
        return requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )
    except:
        return None


def _normalize_google_href(href):
    if not href:
        return None

    if href.startswith("/url?q="):
        link = href.replace("/url?q=", "").split("&")[0]
        link = unquote(link)

        if not link.startswith("http"):
            return None

        if "google." in link:
            return None

        return link

    if href.startswith("http"):
        if "google." in href:
            return None
        return href

    return None


def _extract_google_results(html):
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for a in soup.select("a"):
        href = a.get("href")
        link = _normalize_google_href(href)

        if not link:
            continue

        title = a.get_text(" ", strip=True)
        if not title:
            continue

        results.append({
            "title": title[:200],
            "url": link,
            "snippet": "",
            "source": "google"
        })

    deduped = []
    seen = set()

    for item in results:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        deduped.append(item)

    return deduped


def _search_google(query):
    url = f"https://www.google.com/search?q={quote(query)}&hl=ja&num=10"
    r = fetch(url)

    if not r:
        return []

    return _extract_google_results(r.text)[:10]


def _search_duckduckgo(query):
    url = "https://html.duckduckgo.com/html/"
    r = fetch(url, method="POST", data={"q": query})

    if not r:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    results = []

    for a in soup.select("a.result__a"):
        href = a.get("href")
        title = a.get_text(" ", strip=True)

        if not href or not href.startswith("http"):
            continue

        results.append({
            "title": title[:200] if title else href,
            "url": href,
            "snippet": "",
            "source": "duckduckgo"
        })

    deduped = []
    seen = set()

    for item in results:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        deduped.append(item)

    return deduped[:10]


def search_web(query):
    results = _search_google(query)

    if results:
        return results

    return _search_duckduckgo(query)


def fetch_page_text(url):
    r = fetch(url)

    if not r:
        return ""

    soup = BeautifulSoup(r.text, "html.parser")
    return soup.get_text(separator="\n", strip=True)
