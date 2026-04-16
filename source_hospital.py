# source_hospital.py
# -*- coding: utf-8 -*-

from urllib.parse import quote_plus

from search_provider import search_web_with_meta, get_domain


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


def build_detail_targeted_queries(hospital_name: str):
    hospital_name = hospital_name.strip()
    return [
        f"site:byoinnavi.jp/clinic {hospital_name}",
        f"site:caloo.jp/hospitals/detail {hospital_name}",
        f"site:qlife.jp/hospital_detail {hospital_name}",
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


def _normalize_name(name: str) -> str:
    if not name:
        return ""
    name = "".join(name.split())
    for word in [
        "医療法人",
        "一般財団法人",
        "社会医療法人",
        "医療法人社団",
        "公益財団法人",
        "社会福祉法人",
    ]:
        name = name.replace(word, "")
    return name


def _name_match_score(text: str, hospital_name: str) -> int:
    if not text or not hospital_name:
        return 0

    t = _normalize_name(text)
    h = _normalize_name(hospital_name)

    if not t or not h:
        return 0

    if h in t:
        return 6
    if t in h:
        return 3
    return 0


def _is_detail_url(url: str) -> bool:
    if not url:
        return False

    patterns = [
        "byoinnavi.jp/clinic/",
        "caloo.jp/hospitals/detail/",
        "qlife.jp/hospital_detail_",
    ]
    return any(p in url for p in patterns)


def _is_search_page(url: str) -> bool:
    if not url:
        return False

    patterns = [
        "freeword?q=",
        "/search/all",
        "search_hospital_result",
    ]
    return any(p in url for p in patterns)


def _score_result_row(row: dict, hospital_name: str) -> int:
    url = row.get("url", "")
    title = row.get("title", "")
    snippet = row.get("snippet", "")
    source_type = classify_source(url)

    score = 0

    if _is_detail_url(url):
        score += 10

    if source_type == "official":
        score += 8
    elif source_type == "public":
        score += 6
    elif source_type == "medical-db":
        score += 3

    score += _name_match_score(title, hospital_name)
    score += _name_match_score(snippet, hospital_name)

    if _is_search_page(url):
        score -= 6

    return score


def _collect_from_queries(queries: list, hospital_name: str, query_kind: str, max_urls: int, seen: set):
    rows = []
    query_debug = []

    for q in queries:
        results, metas = search_web_with_meta(q, max_results=5)

        scored = []
        for r in results:
            url = r.get("url", "")
            if not url:
                continue

            scored.append({
                "query": q,
                "title": r.get("title", ""),
                "url": url,
                "snippet": r.get("snippet", ""),
                "provider": r.get("provider", ""),
                "source_type": classify_source(url),
                "domain": get_domain(url),
                "internal_score": _score_result_row(r, hospital_name),
            })

        scored.sort(key=lambda x: x["internal_score"], reverse=True)

        query_debug.append({
            "query_kind": query_kind,
            "query": q,
            "provider_debug": metas,
            "result_count_after_merge": len(results),
            "top_urls": [x["url"] for x in scored[:5]],
        })

        for r in scored:
            url = r.get("url", "")
            if not url or url in seen:
                continue
            seen.add(url)
            rows.append({
                "query": r.get("query", ""),
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("snippet", ""),
                "provider": r.get("provider", ""),
                "source_type": r.get("source_type", ""),
                "domain": r.get("domain", ""),
            })
            if len(rows) >= max_urls:
                return rows, query_debug

    return rows, query_debug


def collect_hospital_candidate_urls(hospital_name: str, debug: bool = False, max_urls: int = 10):
    rows = []
    seen = set()
    query_debug = []

    # 1) 通常検索
    normal_queries = build_hospital_queries(hospital_name)
    normal_rows, normal_debug = _collect_from_queries(
        queries=normal_queries,
        hospital_name=hospital_name,
        query_kind="normal_search",
        max_urls=max_urls,
        seen=seen,
    )
    rows.extend(normal_rows)
    query_debug.extend(normal_debug)

    # 2) 通常検索で詳細URLが弱い場合、詳細URL専用クエリを追加
    has_detail = any(_is_detail_url(r.get("url", "")) for r in rows)
    if not has_detail:
        detail_queries = build_detail_targeted_queries(hospital_name)
        detail_rows, detail_debug = _collect_from_queries(
            queries=detail_queries,
            hospital_name=hospital_name,
            query_kind="detail_targeted_search",
            max_urls=max_urls - len(rows),
            seen=seen,
        )
        rows.extend(detail_rows)
        query_debug.extend(detail_debug)

    # 3) それでも何も取れない場合のみ direct fallback
    if not rows:
        fallback_rows = build_direct_fallback_candidates(hospital_name)
        for r in fallback_rows:
            url = r.get("url", "")
            if not url or url in seen:
                continue
            seen.add(url)
            rows.append(r)

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
