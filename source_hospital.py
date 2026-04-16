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


def build_direct_fallback_candidates(hospital_name: str):
    """
    検索エンジンが0件でも、最低限の候補URLを作る。
    ここでは “候補” を作るだけで、特定はしない。
    """
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

    # 検索エンジンが死んでいた時のみ fallback 候補を追加
    if not rows:
        fallback_rows = build_direct_fallback_candidates(hospital_name)
        for r in fallback_rows:
            url = r.get("url", "")
            if not url or url in seen:
                continue
            seen.add(url)
            rows.append(r)

        query_debug.append({
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
        })

    return {
        "rows": rows[:max_urls],
        "debug": query_debug,
    }
