# source_hospital.py
# -*- coding: utf-8 -*-

import re
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

from search_provider import search_web_with_meta, get_domain, HEADERS


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
        "navitime.co.jp",
        "qlife.jp",
        "medicalnote.jp",
        "fdoc.jp",
    ],
}


def classify_source(url: str) -> str:
    domain = get_domain(url)

    if not domain:
        return "unknown"

    for key, values in TRUSTED_DOMAIN_KEYWORDS.items():
        if any(v in domain for v in values):
            return key

    return "other"


def build_hospital_queries(hospital_name: str):
    hospital_name = hospital_name.strip()
    return [
        f"{hospital_name} 病院 住所",
        f"{hospital_name} 病床数 診療科",
        f"{hospital_name} アクセス 最寄駅",
        f"{hospital_name} 公式",
    ]


def build_direct_fallback_candidates(hospital_name: str):
    q = quote_plus(hospital_name.strip())
    return [
        {
            "query": "direct_fallback",
            "title": f"{hospital_name} - 病院なび 検索候補",
            "url": f"https://byoinnavi.jp/freeword?q={q}",
            "snippet": "",
            "provider": "direct_fallback",
            "source_type": "medical-db",
            "domain": "byoinnavi.jp",
        },
        {
            "query": "direct_fallback",
            "title": f"{hospital_name} - Caloo 検索候補",
            "url": f"https://caloo.jp/search/all?s={q}",
            "snippet": "",
            "provider": "direct_fallback",
            "source_type": "medical-db",
            "domain": "caloo.jp",
        },
        {
            "query": "direct_fallback",
            "title": f"{hospital_name} - QLife 検索候補",
            "url": f"https://www.qlife.jp/search_hospital_result?keyword={q}",
            "snippet": "",
            "provider": "direct_fallback",
            "source_type": "medical-db",
            "domain": "qlife.jp",
        },
    ]


def _safe_request_html(url: str, timeout: int = 8):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.text, None
    except Exception as e:
        return "", str(e)


def _normalize_link(base_url: str, href: str) -> str:
    if not href:
        return ""
    return urljoin(base_url, href.strip())


def _is_likely_hospital_detail_url(url: str, hospital_name: str) -> bool:
    if not url:
        return False

    domain = get_domain(url)

    # 検索結果ページそのものは除外
    if "freeword?q=" in url:
        return False
    if "/search/all" in url:
        return False
    if "search_hospital_result" in url:
        return False

    # DBサイトの個別詳細っぽいURLだけ残す
    if "byoinnavi.jp/clinic/" in url:
        return True
    if "caloo.jp/hospitals/detail/" in url:
        return True
    if "qlife.jp/hospital_detail_" in url:
        return True

    return False


def _extract_byoinnavi_detail_urls(search_url: str, hospital_name: str, max_urls: int = 3):
    html_text, error = _safe_request_html(search_url)
    debug = {
        "source": "byoinnavi_detail_expand",
        "search_url": search_url,
        "status": "ok" if not error else "error",
        "error": error or "",
        "expanded_count": 0,
    }
    if error or not html_text:
        return [], debug

    soup = BeautifulSoup(html_text, "html.parser")
    rows = []
    seen = set()

    for a in soup.select("a[href]"):
        href = _normalize_link(search_url, a.get("href", ""))
        title = a.get_text(" ", strip=True)

        if not _is_likely_hospital_detail_url(href, hospital_name):
            continue
        if href in seen:
            continue

        seen.add(href)
        rows.append({
            "query": "direct_fallback_expanded",
            "title": title or f"{hospital_name} - 病院なび詳細候補",
            "url": href,
            "snippet": "",
            "provider": "direct_fallback_expanded",
            "source_type": "medical-db",
            "domain": get_domain(href),
        })

        if len(rows) >= max_urls:
            break

    debug["expanded_count"] = len(rows)
    return rows, debug


def _extract_caloo_detail_urls(search_url: str, hospital_name: str, max_urls: int = 3):
    html_text, error = _safe_request_html(search_url)
    debug = {
        "source": "caloo_detail_expand",
        "search_url": search_url,
        "status": "ok" if not error else "error",
        "error": error or "",
        "expanded_count": 0,
    }
    if error or not html_text:
        return [], debug

    soup = BeautifulSoup(html_text, "html.parser")
    rows = []
    seen = set()

    for a in soup.select("a[href]"):
        href = _normalize_link(search_url, a.get("href", ""))
        title = a.get_text(" ", strip=True)

        if not _is_likely_hospital_detail_url(href, hospital_name):
            continue
        if href in seen:
            continue

        seen.add(href)
        rows.append({
            "query": "direct_fallback_expanded",
            "title": title or f"{hospital_name} - Caloo詳細候補",
            "url": href,
            "snippet": "",
            "provider": "direct_fallback_expanded",
            "source_type": "medical-db",
            "domain": get_domain(href),
        })

        if len(rows) >= max_urls:
            break

    debug["expanded_count"] = len(rows)
    return rows, debug


def _extract_qlife_detail_urls(search_url: str, hospital_name: str, max_urls: int = 3):
    html_text, error = _safe_request_html(search_url)
    debug = {
        "source": "qlife_detail_expand",
        "search_url": search_url,
        "status": "ok" if not error else "error",
        "error": error or "",
        "expanded_count": 0,
    }
    if error or not html_text:
        return [], debug

    soup = BeautifulSoup(html_text, "html.parser")
    rows = []
    seen = set()

    for a in soup.select("a[href]"):
        href = _normalize_link(search_url, a.get("href", ""))
        title = a.get_text(" ", strip=True)

        if not _is_likely_hospital_detail_url(href, hospital_name):
            continue
        if href in seen:
            continue

        seen.add(href)
        rows.append({
            "query": "direct_fallback_expanded",
            "title": title or f"{hospital_name} - QLife詳細候補",
            "url": href,
            "snippet": "",
            "provider": "direct_fallback_expanded",
            "source_type": "medical-db",
            "domain": get_domain(href),
        })

        if len(rows) >= max_urls:
            break

    debug["expanded_count"] = len(rows)
    return rows, debug


def expand_direct_fallback_candidates(base_rows: list, hospital_name: str):
    expanded = []
    debug_rows = []

    for row in base_rows:
        url = row.get("url", "")
        domain = row.get("domain", "")

        if "byoinnavi.jp" in domain:
            rows, dbg = _extract_byoinnavi_detail_urls(url, hospital_name, max_urls=3)
            expanded.extend(rows)
            debug_rows.append(dbg)

        elif "caloo.jp" in domain:
            rows, dbg = _extract_caloo_detail_urls(url, hospital_name, max_urls=3)
            expanded.extend(rows)
            debug_rows.append(dbg)

        elif "qlife.jp" in domain:
            rows, dbg = _extract_qlife_detail_urls(url, hospital_name, max_urls=3)
            expanded.extend(rows)
            debug_rows.append(dbg)

    return expanded, debug_rows


def collect_hospital_candidate_urls(hospital_name: str, debug: bool = False, max_urls: int = 10):
    queries = build_hospital_queries(hospital_name)

    rows = []
    seen = set()
    query_debug = []

    for q in queries:
        results, metas = search_web_with_meta(q, max_results=4)

        query_debug.append({
            "query": q,
            "provider_debug": metas,
            "result_count_after_merge": len(results),
        })

        for r in results:
            url = r.get("url", "")
            if not url or url in seen:
                continue

            seen.add(url)
            rows.append({
                "query": q,
                "title": r.get("title", ""),
                "url": url,
                "snippet": r.get("snippet", ""),
                "provider": r.get("provider", ""),
                "source_type": classify_source(url),
                "domain": get_domain(url),
            })

            if len(rows) >= max_urls:
                return {
                    "rows": rows,
                    "debug": query_debug,
                }

    # 検索エンジンが死んでいる時のみ direct fallback
    if not rows:
        fallback_rows = build_direct_fallback_candidates(hospital_name)
        expanded_rows, expand_debug = expand_direct_fallback_candidates(fallback_rows, hospital_name)

        query_debug.append({
            "query": "direct_fallback_base",
            "provider_debug": [{
                "provider": "direct_fallback_base",
                "status": "used",
                "result_count": len(fallback_rows),
                "error": "",
                "http_status": None,
                "sample_url": fallback_rows[0]["url"] if fallback_rows else "",
            }],
            "result_count_after_merge": len(fallback_rows),
        })

        query_debug.append({
            "query": "direct_fallback_expanded",
            "provider_debug": expand_debug,
            "result_count_after_merge": len(expanded_rows),
        })

        candidate_source = expanded_rows if expanded_rows else fallback_rows

        for r in candidate_source:
            url = r.get("url", "")
            if not url or url in seen:
                continue
            seen.add(url)
            rows.append(r)

    return {
        "rows": rows[:max_urls],
        "debug": query_debug,
    }
