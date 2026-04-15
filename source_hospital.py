# -*- coding: utf-8 -*-
from urllib.parse import urlparse

from search_provider import search_web


PORTAL_KEYWORDS = [
    "caloo",
    "byoinnavi",
    "medicalnote",
    "qlife",
    "scuel",
    "fdoc",
    "epark",
    "navitime"
]

JOB_KEYWORDS = [
    "indeed",
    "townwork",
    "rikunabi",
    "job-medley",
    "staffservice",
    "manpower",
    "hatarako",
    "baitoru",
    "en-gage",
    "career"
]


def classify_source(url):
    host = urlparse(url).netloc.lower()

    if "wikipedia.org" in host:
        return "wiki"

    for kw in PORTAL_KEYWORDS:
        if kw in host:
            return "portal"

    for kw in JOB_KEYWORDS:
        if kw in host:
            return "job"

    if host.endswith(".or.jp") or host.endswith(".jp"):
        return "official"

    return "other"


def is_hospital_candidate(url):
    source = classify_source(url)
    return source != "job"


def source_priority(source):
    if source == "official":
        return 4
    if source == "portal":
        return 3
    if source == "wiki":
        return 2
    if source == "other":
        return 1
    return 0


def build_queries(name, area=""):
    queries = []

    base_terms = [
        "病院",
        "病院 住所",
        "病院 アクセス",
        "病院 所在地",
        "医療法人",
        "病院 外来",
        "病院 入院"
    ]

    portal_sites = [
        "byoinnavi.jp",
        "caloo.jp",
        "qlife.jp",
        "medicalnote.jp",
        "scuel.me"
    ]

    if area:
        for term in base_terms:
            queries.append(f"{name} {area} {term}")

        for site in portal_sites:
            queries.append(f"site:{site} {name} {area}")
    else:
        for term in base_terms:
            queries.append(f"{name} {term}")

        for site in portal_sites:
            queries.append(f"site:{site} {name}")

    # 公式系狙い
    if area:
        queries.append(f"{name} {area} site:or.jp")
        queries.append(f"{name} {area} site:jp")
    else:
        queries.append(f"{name} site:or.jp")
        queries.append(f"{name} site:jp")

    # 重複除去
    deduped = []
    seen = set()

    for q in queries:
        if q in seen:
            continue
        seen.add(q)
        deduped.append(q)

    return deduped


def score_search_item(item, name, area=""):
    score = 0

    title = str(item.get("title", ""))
    url = str(item.get("url", ""))
    source = item.get("source", "")

    score += source_priority(source) * 20

    if name and name in title:
        score += 30

    if area:
        if area in title or area in url:
            score += 20

    # ポータルや公式で病院っぽさを加点
    keywords = ["病院", "医院", "クリニック", "医療法人", "診療科", "アクセス", "入院"]
    for kw in keywords:
        if kw in title:
            score += 5

    return score


def search_hospital_candidate_urls(name, area=""):
    queries = build_queries(name, area)
    results = []

    for query in queries:
        items = search_web(query)

        for item in items:
            url = item.get("url", "")
            if not url:
                continue

            if not is_hospital_candidate(url):
                continue

            source = classify_source(url)

            scored_item = {
                "title": item.get("title", ""),
                "url": url,
                "snippet": item.get("snippet", ""),
                "source": source,
            }
            scored_item["score"] = score_search_item(scored_item, name, area)

            results.append(scored_item)

    # URL重複除去しつつ高得点を残す
    best_by_url = {}

    for item in results:
        url = item["url"]

        if url not in best_by_url:
            best_by_url[url] = item
            continue

        if item["score"] > best_by_url[url]["score"]:
            best_by_url[url] = item

    deduped = list(best_by_url.values())
    deduped.sort(key=lambda x: x.get("score", 0), reverse=True)

    return deduped[:15]
