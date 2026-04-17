# source_hospital.py
# -*- coding: utf-8 -*-

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
        return 8
    if t in h:
        return 4
    return 0


def _score_result_row(title: str, snippet: str, url: str, hospital_name: str) -> int:
    score = 0

    source_type = classify_source(url)
    if source_type == "official":
        score += 12
    elif source_type == "public":
        score += 10
    elif source_type == "medical-db":
        score += 5
    else:
        score += 1

    if _is_detail_url(url):
        score += 15

    if _is_search_page(url):
        score -= 20

    score += _name_match_score(title, hospital_name)
    score += _name_match_score(snippet, hospital_name)

    if "病院" in (title or ""):
        score += 1

    return score


def build_queries(hospital_name: str):
    hospital_name = hospital_name.strip()
    return [
        f"{hospital_name} 公式",
        f"{hospital_name} 病院 住所",
        f"{hospital_name} site:byoinnavi.jp/clinic",
        f"{hospital_name} site:caloo.jp/hospitals/detail",
        f"{hospital_name} site:qlife.jp/hospital_detail",
        f"{hospital_name} site:medicalnote.jp/hospitals",
    ]


def search_hospital_candidates(hospital_name: str, max_urls: int = 10):
    seen = set()
    candidates = []
    query_debug = []

    queries = build_queries(hospital_name)

    for q in queries:
        results, metas = search_web_with_meta(q, max_results=6)

        scored = []
        for r in results:
            url = r.get("url", "")
            if not url:
                continue

            title = r.get("title", "")
            snippet = r.get("snippet", "")

            score = _score_result_row(title, snippet, url, hospital_name)

            # 検索ページは禁止
            if _is_search_page(url):
                continue

            # 候補は詳細URL or 公式/公的ページのみ
            source_type = classify_source(url)
            if not _is_detail_url(url) and source_type not in ["official", "public"]:
                continue

            scored.append({
                "query": q,
                "title": title,
                "url": url,
                "snippet": snippet,
                "provider": r.get("provider", ""),
                "source_type": source_type,
                "domain": get_domain(url),
                "internal_score": score,
            })

        scored.sort(key=lambda x: x["internal_score"], reverse=True)

        query_debug.append({
            "query": q,
            "provider_debug": metas,
            "accepted_urls": [x["url"] for x in scored[:5]],
            "accepted_count": len(scored),
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
            })
            if len(candidates) >= max_urls:
                break

        if len(candidates) >= max_urls:
            break

    return {
        "rows": candidates[:max_urls],
        "debug": query_debug,
    }
