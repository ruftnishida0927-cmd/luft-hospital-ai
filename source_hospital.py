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


def _detail_patterns_for_domain(domain: str):
    if "byoinnavi.jp" in domain:
        return [r"https?://byoinnavi\.jp/clinic/\d+", r"/clinic/\d+"]
    if "caloo.jp" in domain:
        return [r"https?://caloo\.jp/hospitals/detail/[A-Za-z0-9]+", r"/hospitals/detail/[A-Za-z0-9]+"]
    if "qlife.jp" in domain:
        return [r"https?://(?:www\.)?qlife\.jp/hospital_detail_\d+", r"/hospital_detail_\d+"]
    return []


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


def _extract_candidate_texts(a_tag):
    texts = []

    own_text = a_tag.get_text(" ", strip=True)
    if own_text:
        texts.append(own_text)

    title_attr = a_tag.get("title", "")
    if title_attr:
        texts.append(title_attr)

    aria_label = a_tag.get("aria-label", "")
    if aria_label:
        texts.append(aria_label)

    parent = a_tag.parent
    if parent:
        parent_text = parent.get_text(" ", strip=True)
        if parent_text:
            texts.append(parent_text)

    return texts


def _extract_anchor_detail_urls(search_url: str, hospital_name: str, soup: BeautifulSoup, max_urls: int = 10):
    rows = []
    seen = set()
    matched_texts = []

    for a in soup.select("a[href]"):
        href = _normalize_link(search_url, a.get("href", ""))
        if not href:
            continue

        if not _is_likely_hospital_detail_url(href):
            continue

        candidate_texts = _extract_candidate_texts(a)
        text_match = any(_name_matches(t, hospital_name) for t in candidate_texts)

        # URLに病院名がなくても、anchor近辺テキストが一致すれば採用
        if not text_match:
            continue

        if href in seen:
            continue

        seen.add(href)
        title = a.get_text(" ", strip=True) or a.get("title", "").strip()
        if not title:
            title = f"{hospital_name} 詳細候補"

        rows.append({
            "query": "direct_fallback_expanded",
            "title": title,
            "url": href,
            "snippet": "",
            "provider": "direct_fallback_expanded_anchor",
            "source_type": "medical-db",
            "domain": get_domain(href),
        })
        matched_texts.append(title)

        if len(rows) >= max_urls:
            break

    return rows, matched_texts


def _extract_regex_detail_urls(search_url: str, hospital_name: str, html_text: str, domain: str, max_urls: int = 10):
    patterns = _detail_patterns_for_domain(domain)
    found = []
    seen = set()

    normalized_html = html.unescape(html_text)

    for pat in patterns:
        for m in re.finditer(pat, normalized_html):
            raw_url = m.group(0)
            full_url = _normalize_link(search_url, raw_url)

            if not _is_likely_hospital_detail_url(full_url):
                continue
            if full_url in seen:
                continue

            # 近傍テキストに病院名があるか確認
            start = max(0, m.start() - 250)
            end = min(len(normalized_html), m.end() + 250)
            context = normalized_html[start:end]

            if not _name_matches(context, hospital_name):
                # 近傍テキストで一致しなくても、一旦候補として少数だけ残す
                # ただし domainごとに最初の1件までに抑える
                if len(found) >= 1:
                    continue

            seen.add(full_url)
            found.append({
                "query": "direct_fallback_expanded",
                "title": f"{hospital_name} 詳細候補",
                "url": full_url,
                "snippet": "",
                "provider": "direct_fallback_expanded_regex",
                "source_type": "medical-db",
                "domain": get_domain(full_url),
            })

            if len(found) >= max_urls:
                break

        if len(found) >= max_urls:
            break

    return found


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
        "matched_anchor_texts": [],
    }

    if error or not html_text:
        return [], debug

    soup = BeautifulSoup(html_text, "html.parser")
    domain = get_domain(search_url)

    anchor_rows, matched_anchor_texts = _extract_anchor_detail_urls(
        search_url=search_url,
        hospital_name=hospital_name,
        soup=soup,
        max_urls=max_urls,
    )
    regex_rows = _extract_regex_detail_urls(
        search_url=search_url,
        hospital_name=hospital_name,
        html_text=html_text,
        domain=domain,
        max_urls=max_urls,
    )

    merged = []
    seen = set()

    for row in anchor_rows + regex_rows:
        u = row.get("url", "")
        if not u or u in seen:
            continue
        seen.add(u)
        merged.append(row)
        if len(merged) >= max_urls:
            break

    debug["anchor_found_count"] = len(anchor_rows)
    debug["anchor_found_urls"] = [r["url"] for r in anchor_rows]
    debug["regex_found_count"] = len(regex_rows)
    debug["regex_found_urls"] = [r["url"] for r in regex_rows]
    debug["final_expanded_count"] = len(merged)
    debug["final_expanded_urls"] = [r["url"] for r in merged]
    debug["matched_anchor_texts"] = matched_anchor_texts[:10]

    return merged, debug


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
                "matched_anchor_texts": [],
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

    # 1) 通常検索
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

    # 2) 通常検索がダメなら fallback
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
