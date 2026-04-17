# source_hospital.py
# -*- coding: utf-8 -*-

import os
import re
import html
from typing import List, Dict, Any

import requests


SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


TRUSTED_DOMAIN_KEYWORDS = {
    "official": [
        ".or.jp",
        ".hospital",
        ".hp.",
        ".med.",
    ],
    "public": [
        "pref.",
        "city.",
        "lg.jp",
        "mhlw.go.jp",
    ],
    "medical-db": [
        "byoinnavi.jp",
        "caloo.jp",
        "qlife.jp",
        "medicalnote.jp",
        "fdoc.jp",
    ],
}


def get_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def classify_source(url: str) -> str:
    domain = get_domain(url)
    if not domain:
        return "unknown"

    for key, values in TRUSTED_DOMAIN_KEYWORDS.items():
        if any(v in domain for v in values):
            return key

    return "other"


def _normalize_name(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"\s+", "", text)
    for word in [
        "医療法人",
        "一般財団法人",
        "社会医療法人",
        "医療法人社団",
        "公益財団法人",
        "社会福祉法人",
    ]:
        text = text.replace(word, "")
    return text


def _name_match_score(text: str, hospital_name: str) -> int:
    if not text or not hospital_name:
        return 0

    t = _normalize_name(text)
    h = _normalize_name(hospital_name)

    if not t or not h:
        return 0

    if h in t:
        return 8
    if t in h:
        return 4
    return 0


def _is_detail_url(url: str) -> bool:
    if not url:
        return False

    detail_patterns = [
        "byoinnavi.jp/clinic/",
        "caloo.jp/hospitals/detail/",
        "qlife.jp/hospital_detail_",
        "medicalnote.jp/hospitals/",
        "fdoc.jp/clinic/detail/",
    ]
    return any(p in url for p in detail_patterns)


def _is_search_page(url: str) -> bool:
    if not url:
        return False

    search_patterns = [
        "freeword?q=",
        "/search/all",
        "search_hospital_result",
        "/search?",
        "/search/",
    ]
    return any(p in url for p in search_patterns)


def _build_queries(hospital_name: str, prefecture: str = "") -> List[str]:
    base = hospital_name.strip()
    area = prefecture.strip()

    queries = [
        f"{base} {area} 公式".strip(),
        f"{base} {area} 病院 住所".strip(),
        f"{base} {area} site:byoinnavi.jp/clinic".strip(),
        f"{base} {area} site:caloo.jp/hospitals/detail".strip(),
        f"{base} {area} site:qlife.jp/hospital_detail".strip(),
        f"{base} {area} site:medicalnote.jp/hospitals".strip(),
    ]
    return queries


def _serpapi_search(query: str, max_results: int = 10) -> Dict[str, Any]:
    api_key = os.getenv("SERPAPI_API_KEY", "").strip()
    if not api_key:
        return {
            "ok": False,
            "error": "SERPAPI_API_KEY が未設定です。",
            "results": [],
        }

    params = {
        "engine": "google",
        "q": query,
        "hl": "ja",
        "gl": "jp",
        "google_domain": "google.co.jp",
        "api_key": api_key,
        "num": max_results,
    }

    try:
        r = requests.get(SERPAPI_ENDPOINT, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()

        organic = data.get("organic_results", []) or []
        results = []
        for row in organic:
            results.append({
                "title": row.get("title", "") or "",
                "url": row.get("link", "") or "",
                "snippet": row.get("snippet", "") or "",
                "provider": "serpapi",
            })

        return {
            "ok": True,
            "error": "",
            "results": results,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "results": [],
        }


def _score_result_row(title: str, snippet: str, url: str, hospital_name: str, prefecture: str = "") -> int:
    score = 0

    source_type = classify_source(url)
    if source_type == "official":
        score += 12
    elif source_type == "public":
        score += 10
    elif source_type == "medical-db":
        score += 6
    else:
        score += 1

    if _is_detail_url(url):
        score += 15

    if _is_search_page(url):
        score -= 20

    score += _name_match_score(title, hospital_name)
    score += _name_match_score(snippet, hospital_name)

    if prefecture:
        if prefecture in title:
            score += 4
        if prefecture in snippet:
            score += 4
        if prefecture in url:
            score += 2

    if "病院" in (title or ""):
        score += 1

    return score


def search_hospital_candidates(hospital_name: str, prefecture: str = "", max_urls: int = 10) -> Dict[str, Any]:
    seen = set()
    candidates = []
    query_debug = []

    queries = _build_queries(hospital_name, prefecture)

    for q in queries:
        resp = _serpapi_search(q, max_results=10)
        raw_results = resp.get("results", [])

        scored = []
        for r in raw_results:
            url = r.get("url", "")
            if not url:
                continue

            if _is_search_page(url):
                continue

            source_type = classify_source(url)
            if not _is_detail_url(url) and source_type not in ["official", "public"]:
                continue

            title = r.get("title", "")
            snippet = r.get("snippet", "")
            score = _score_result_row(title, snippet, url, hospital_name, prefecture)

            scored.append({
                "query": q,
                "title": title,
                "url": url,
                "snippet": snippet,
                "provider": r.get("provider", "serpapi"),
                "source_type": source_type,
                "domain": get_domain(url),
                "internal_score": score,
            })

        scored.sort(key=lambda x: x["internal_score"], reverse=True)

        query_debug.append({
            "query": q,
            "ok": resp.get("ok", False),
            "error": resp.get("error", ""),
            "accepted_count": len(scored),
            "accepted_urls": [x["url"] for x in scored[:5]],
        })

        for row in scored:
            url = row["url"]
            if url in seen:
                continue
            seen.add(url)
            candidates.append({
                "query": row["query"],
                "title": row["title"],
                "url": row["url"],
                "snippet": row["snippet"],
                "provider": row["provider"],
                "source_type": row["source_type"],
                "domain": row["domain"],
                "internal_score": row["internal_score"],
            })
            if len(candidates) >= max_urls:
                break

        if len(candidates) >= max_urls:
            break

    return {
        "rows": candidates[:max_urls],
        "debug": query_debug,
    }
