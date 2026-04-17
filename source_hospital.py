# source_hospital.py
# -*- coding: utf-8 -*-

import re
import html
from urllib.parse import quote_plus, urljoin, unquote

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

    patterns = [
        "byoinnavi.jp/clinic/",
        "caloo.jp/hospitals/detail/",
        "qlife.jp/hospital_detail_",
        "medicalnote.jp/hospitals/",
        "fdoc.jp/clinic/detail/",
    ]
    return any(p in url for p in patterns)


def _is_search_page(url: str) -> bool:
    if not url:
        return False

    patterns = [
        "freeword?q=",
        "/search/all",
        "search_hospital_result",
        "search?",
        "/search/",
    ]
    return any(p in url for p in patterns)


def build_normal_queries(hospital_name: str):
    hospital_name = hospital_name.strip()
    return [
        f"{hospital_name} 病院 住所",
        f"{hospital_name} 病床数 診療科",
        f"{hospital_name} アクセス 最寄駅",
        f"{hospital_name} 公式",
    ]


def build_detail_targeted_queries(hospital_name: str):
    hospital_name = hospital_name.strip()
    return [
        f"site:byoinnavi.jp/clinic {hospital_name}",
        f"site:caloo.jp/hospitals/detail {hospital_name}",
        f"site:qlife.jp/hospital_detail {hospital_name}",
        f"site:medicalnote.jp/hospitals {hospital_name}",
    ]


def build_direct_site_search_pages(hospital_name: str):
    q = quote_plus(hospital_name.strip())
    return [
        {
            "site": "byoinnavi",
            "url": f"https://byoinnavi.jp/freeword?q={q}",
        },
        {
            "site": "caloo",
            "url": f"https://caloo.jp/search/all?s={q}",
        },
        {
            "site": "qlife",
            "url": f"https://www.qlife.jp/search_hospital_result?keyword={q}",
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


def _score_candidate_row(title: str, snippet: str, url: str, hospital_name: str) -> int:
    score = 0

    source_type = classify_source(url)
    if source_type == "official":
        score += 10
    elif source_type == "public":
        score += 8
    elif source_type == "medical-db":
        score += 4
    else:
        score += 1

    if _is_detail_url(url):
        score += 12

    if _is_search_page(url):
        score -= 8

    score += _name_match_score(title, hospital_name)
    score += _name_match_score(snippet, hospital_name)

    if "病院" in (title or ""):
        score += 1
    if "病院" in (snippet or ""):
        score += 1

    return score


def _collect_from_search_queries(queries, hospital_name: str, query_kind: str, max_urls: int, seen: set):
    rows = []
    debug_rows = []

    for q in queries:
        results, metas = search_web_with_meta(q, max_results=5)

        scored = []
        for r in results:
            url = r.get("url", "")
            if not url:
                continue

            title = r.get("title", "")
            snippet = r.get("snippet", "")

            scored.append({
                "query": q,
                "title": title,
                "url": url,
                "snippet": snippet,
                "provider": r.get("provider", ""),
                "source_type": classify_source(url),
                "domain": get_domain(url),
                "internal_score": _score_candidate_row(title, snippet, url, hospital_name),
            })

        scored.sort(key=lambda x: x["internal_score"], reverse=True)

        debug_rows.append({
            "query_kind": query_kind,
            "query": q,
            "provider_debug": metas,
            "result_count_after_merge": len(results),
            "top_urls": [x["url"] for x in scored[:5]],
        })

        for row in scored:
            url = row.get("url", "")
            if not url or url in seen:
                continue

            seen.add(url)
            rows.append({
                "query": row.get("query", ""),
                "title": row.get("title", ""),
                "url": row.get("url", ""),
                "snippet": row.get("snippet", ""),
                "provider": row.get("provider", ""),
                "source_type": row.get("source_type", ""),
                "domain": row.get("domain", ""),
            })

            if len(rows) >= max_urls:
                return rows, debug_rows

    return rows, debug_rows


def _detail_patterns_for_site(site_name: str):
    if site_name == "byoinnavi":
        return [
            r"https?://byoinnavi\.jp/clinic/\d+",
            r"/clinic/\d+",
        ]
    if site_name == "caloo":
        return [
            r"https?://caloo\.jp/hospitals/detail/[A-Za-z0-9]+",
            r"/hospitals/detail/[A-Za-z0-9]+",
        ]
    if site_name == "qlife":
        return [
            r"https?://(?:www\.)?qlife\.jp/hospital_detail_\d+",
            r"/hospital_detail_\d+",
        ]
    return []


def _extract_detail_urls_from_site_search(site_name: str, search_url: str, hospital_name: str, max_urls: int = 10):
    html_text, error = _safe_request_html(search_url)

    debug = {
        "query_kind": "direct_site_search",
        "site": site_name,
        "search_url": search_url,
        "status": "ok" if not error else "error",
        "error": error or "",
        "anchor_found_urls": [],
        "regex_found_urls": [],
        "final_urls": [],
    }

    if error or not html_text:
        return [], debug

    soup = BeautifulSoup(html_text, "html.parser")
    normalized_html = html.unescape(html_text)

    candidates = []
    seen = set()

    # 1) anchorベース
    for a in soup.select("a[href]"):
        href = _normalize_link(search_url, a.get("href", ""))
        if not href or href in seen:
            continue
        if not _is_detail_url(href):
            continue

        title = a.get_text(" ", strip=True) or a.get("title", "").strip()
        parent_text = a.parent.get_text(" ", strip=True) if a.parent else ""
        snippet = f"{title} {parent_text}".strip()

        score = _score_candidate_row(title, snippet, href, hospital_name)
        candidates.append({
            "title": title or f"{hospital_name} 詳細候補",
            "url": href,
            "snippet": snippet[:300],
            "provider": "direct_site_search_anchor",
            "source_type": classify_source(href),
            "domain": get_domain(href),
            "internal_score": score,
        })
        seen.add(href)

    debug["anchor_found_urls"] = [x["url"] for x in candidates[:10]]

    # 2) regexベース
    regex_urls = []
    patterns = _detail_patterns_for_site(site_name)
    for pat in patterns:
        for m in re.finditer(pat, normalized_html):
            raw = m.group(0)
            href = _normalize_link(search_url, raw)
            if not href or href in seen:
                continue
            if not _is_detail_url(href):
                continue

            start = max(0, m.start() - 250)
            end = min(len(normalized_html), m.end() + 250)
            snippet = normalized_html[start:end]

            score = _score_candidate_row("", snippet, href, hospital_name)
            candidates.append({
                "title": f"{hospital_name} 詳細候補",
                "url": href,
                "snippet": snippet[:300],
                "provider": "direct_site_search_regex",
                "source_type": classify_source(href),
                "domain": get_domain(href),
                "internal_score": score,
            })
            seen.add(href)
            regex_urls.append(href)

    debug["regex_found_urls"] = regex_urls[:10]

    # 3) スコア順
    dedup = {}
    for row in candidates:
        u = row["url"]
        if u not in dedup or row["internal_score"] > dedup[u]["internal_score"]:
            dedup[u] = row

    final_rows = sorted(dedup.values(), key=lambda x: x["internal_score"], reverse=True)[:max_urls]
    debug["final_urls"] = [x["url"] for x in final_rows[:10]]

    rows = []
    for row in final_rows:
        rows.append({
            "query": f"direct_site_search:{site_name}",
            "title": row.get("title", ""),
            "url": row.get("url", ""),
            "snippet": row.get("snippet", ""),
            "provider": row.get("provider", ""),
            "source_type": row.get("source_type", ""),
            "domain": row.get("domain", ""),
        })

    return rows, debug


def _collect_from_direct_site_search(hospital_name: str, max_urls: int, seen: set):
    rows = []
    debug_rows = []

    pages = build_direct_site_search_pages(hospital_name)
    for page in pages:
        site_name = page["site"]
        search_url = page["url"]

        extracted_rows, dbg = _extract_detail_urls_from_site_search(
            site_name=site_name,
            search_url=search_url,
            hospital_name=hospital_name,
            max_urls=5,
        )
        debug_rows.append(dbg)

        for row in extracted_rows:
            url = row.get("url", "")
            if not url or url in seen:
                continue
            seen.add(url)
            rows.append(row)

            if len(rows) >= max_urls:
                return rows, debug_rows

    return rows, debug_rows


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


def collect_hospital_candidate_urls(hospital_name: str, debug: bool = False, max_urls: int = 10):
    rows = []
    seen = set()
    query_debug = []

    # A. 通常検索
    normal_rows, normal_debug = _collect_from_search_queries(
        queries=build_normal_queries(hospital_name),
        hospital_name=hospital_name,
        query_kind="normal_search",
        max_urls=max_urls,
        seen=seen,
    )
    rows.extend(normal_rows)
    query_debug.extend(normal_debug)

    # B. 詳細URL狙い検索
    has_detail = any(_is_detail_url(r.get("url", "")) for r in rows)
    if not has_detail:
        detail_rows, detail_debug = _collect_from_search_queries(
            queries=build_detail_targeted_queries(hospital_name),
            hospital_name=hospital_name,
            query_kind="detail_targeted_search",
            max_urls=max_urls - len(rows),
            seen=seen,
        )
        rows.extend(detail_rows)
        query_debug.extend(detail_debug)

    # C. 医療DB内部検索を直接解析
    has_detail = any(_is_detail_url(r.get("url", "")) for r in rows)
    if not has_detail:
        direct_rows, direct_debug = _collect_from_direct_site_search(
            hospital_name=hospital_name,
            max_urls=max_urls - len(rows),
            seen=seen,
        )
        rows.extend(direct_rows)
        query_debug.extend(direct_debug)

    # D. それでも何もなければ検索ページを最後の候補として出す
    if not rows:
        fallback_rows = build_direct_fallback_candidates(hospital_name)
        for row in fallback_rows:
            url = row.get("url", "")
            if not url or url in seen:
                continue
            seen.add(url)
            rows.append(row)

        query_debug.append({
            "query_kind": "direct_fallback",
            "query": "direct_fallback",
            "provider_debug": [{
                "provider": "direct_fallback",
                "status": "used",
                "result_count": len(rows),
                "error": "",
                "http_status": None,
                "sample_url": rows[0]["url"] if rows else "",
            }],
            "result_count_after_merge": len(rows),
            "top_urls": [r["url"] for r in rows[:5]],
        })

    return {
        "rows": rows[:max_urls],
        "debug": query_debug,
    }
