# source_hospital.py
# -*- coding: utf-8 -*-

import re
import html
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


def _normalize_name(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"\s+", "", text)
    text = text.replace("医療法人", "")
    text = text.replace("一般財団法人", "")
    text = text.replace("社会医療法人", "")
    text = text.replace("医療法人社団", "")
    text = text.replace("公益財団法人", "")
    text = text.replace("社会福祉法人", "")
    return text


def _name_matches(candidate_text: str, hospital_name: str) -> bool:
    if not candidate_text or not hospital_name:
        return False

    c = _normalize_name(candidate_text)
    h = _normalize_name(hospital_name)

    if not c or not h:
        return False

    return h in c or c in h


def _is_search_result_page(url: str) -> bool:
    if not url:
        return False

    patterns = [
        "freeword?q=",
        "/search/all",
        "search_hospital_result",
    ]
    return any(p in url for p in patterns)


def _is_likely_hospital_detail_url(url: str) -> bool:
    if not url:
        return False

    if _is_search_result_page(url):
        return False

    detail_patterns = [
        "byoinnavi.jp/clinic/",
        "caloo.jp/hospitals/detail/",
        "qlife.jp/hospital_detail_",
    ]
    return any(p in url for p in detail_patterns)


def _detail_patterns_for_domain(domain: str):
    if "byoinnavi.jp" in domain:
        return [
            r"https?://byoinnavi\.jp/clinic/\d+",
            r"/clinic/\d+",
        ]
    if "caloo.jp" in domain:
        return [
            r"https?://caloo\.jp/hospitals/detail/[A-Za-z0-9]+",
            r"/hospitals/detail/[A-Za-z0-9]+",
        ]
    if "qlife.jp" in domain:
        return [
            r"https?://(?:www\.)?qlife\.jp/hospital_detail_\d+",
            r"/hospital_detail_\d+",
        ]
    return []


def _score_detail_candidate(url: str, title: str, context: str, hospital_name: str) -> int:
    score = 0

    if _is_likely_hospital_detail_url(url):
        score += 5

    if title and _name_matches(title, hospital_name):
        score += 6

    if context and _name_matches(context, hospital_name):
        score += 5

    if "病院" in (title or ""):
        score += 1

    if "病院" in (context or ""):
        score += 1

    return score


def _extract_anchor_candidates(search_url: str, hospital_name: str, soup: BeautifulSoup, max_urls: int = 20):
    rows = []
    seen = set()

    for a in soup.select("a[href]"):
        href = _normalize_link(search_url, a.get("href", ""))
        if not href or href in seen:
            continue

        if not _is_likely_hospital_detail_url(href):
            continue

        seen.add(href)

        title = a.get_text(" ", strip=True) or a.get("title", "").strip()
        parent_text = a.parent.get_text(" ", strip=True) if a.parent else ""
        context = f"{title} {parent_text}".strip()

        score = _score_detail_candidate(
            url=href,
            title=title,
            context=context,
            hospital_name=hospital_name,
        )

        rows.append({
            "url": href,
            "title": title or f"{hospital_name} 詳細候補",
            "context": context[:300],
            "score": score,
            "provider": "direct_fallback_expanded_anchor",
        })

        if len(rows) >= max_urls:
            break

    return rows


def _extract_regex_candidates(search_url: str, hospital_name: str, html_text: str, domain: str, max_urls: int = 20):
    rows = []
    seen = set()

    normalized_html = html.unescape(html_text)
    patterns = _detail_patterns_for_domain(domain)

    for pat in patterns:
        for m in re.finditer(pat, normalized_html):
            raw_url = m.group(0)
            href = _normalize_link(search_url, raw_url)

            if not href or href in seen:
                continue

            if not _is_likely_hospital_detail_url(href):
                continue

            seen.add(href)

            start = max(0, m.start() - 300)
            end = min(len(normalized_html), m.end() + 300)
            context = normalized_html[start:end]

            score = _score_detail_candidate(
                url=href,
                title="",
                context=context,
                hospital_name=hospital_name,
            )

            rows.append({
                "url": href,
                "title": f"{hospital_name} 詳細候補",
                "context": context[:300],
                "score": score,
                "provider": "direct_fallback_expanded_regex",
            })

            if len(rows) >= max_urls:
                break

        if len(rows) >= max_urls:
            break

    return rows


def _merge_scored_candidates(candidates: list, max_urls: int = 5):
    if not candidates:
        return []

    merged = {}
    for row in candidates:
        url = row["url"]
        if url not in merged:
            merged[url] = row
        else:
            if row["score"] > merged[url]["score"]:
                merged[url] = row

    result = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
    return result[:max_urls]


def _expand_one_search_page(search_url: str, hospital_name: str, site_name: str, max_urls: int = 5):
    html_text, error = _safe_request_html(search_url)

    debug = {
        "source": f"{site_name}_detail_expand",
        "search_url": search_url,
        "status": "ok" if not error else "error",
        "error": error or "",
        "anchor_found_count": 0,
        "anchor_found_urls": [],
        "regex_found_count": 0,
        "regex_found_urls": [],
        "final_expanded_count": 0,
        "final_expanded_urls": [],
    }

    if error or not html_text:
        return [], debug

    soup = BeautifulSoup(html_text, "html.parser")
    domain = get_domain(search_url)

    anchor_candidates = _extract_anchor_candidates(
        search_url=search_url,
        hospital_name=hospital_name,
        soup=soup,
        max_urls=20,
    )

    regex_candidates = _extract_regex_candidates(
        search_url=search_url,
        hospital_name=hospital_name,
        html_text=html_text,
        domain=domain,
        max_urls=20,
    )

    final_candidates = _merge_scored_candidates(anchor_candidates + regex_candidates, max_urls=max_urls)

    debug["anchor_found_count"] = len(anchor_candidates)
    debug["anchor_found_urls"] = [r["url"] for r in anchor_candidates[:10]]
    debug["regex_found_count"] = len(regex_candidates)
    debug["regex_found_urls"] = [r["url"] for r in regex_candidates[:10]]
    debug["final_expanded_count"] = len(final_candidates)
    debug["final_expanded_urls"] = [r["url"] for r in final_candidates[:10]]

    rows = []
    for row in final_candidates:
        rows.append({
            "query": "direct_fallback_expanded",
            "title": row["title"],
            "url": row["url"],
            "snippet": "",
            "provider": row["provider"],
            "source_type": "medical-db",
            "domain": get_domain(row["url"]),
        })

    return rows, debug


def expand_direct_fallback_candidates(base_rows: list, hospital_name: str):
    expanded = []
    debug_rows = []
    seen = set()

    for row in base_rows:
        url = row.get("url", "")
        domain = row.get("domain", "")

        if "byoinnavi.jp" in domain:
            rows, dbg = _expand_one_search_page(url, hospital_name, "byoinnavi", max_urls=5)
        elif "caloo.jp" in domain:
            rows, dbg = _expand_one_search_page(url, hospital_name, "caloo", max_urls=5)
        elif "qlife.jp" in domain:
            rows, dbg = _expand_one_search_page(url, hospital_name, "qlife", max_urls=5)
        else:
            rows, dbg = [], {
                "source": f"{domain}_detail_expand",
                "search_url": url,
                "status": "skipped",
                "error": "",
                "anchor_found_count": 0,
                "anchor_found_urls": [],
                "regex_found_count": 0,
                "regex_found_urls": [],
                "final_expanded_count": 0,
                "final_expanded_urls": [],
            }

        debug_rows.append(dbg)

        for r in rows:
            detail_url = r.get("url", "")
            if not detail_url or detail_url in seen:
                continue
            seen.add(detail_url)
            expanded.append(r)

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
