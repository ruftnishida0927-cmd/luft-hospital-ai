# -*- coding: utf-8 -*-
from urllib.parse import urlparse

from search_provider import search_web


PORTAL_KEYWORDS = [
    "caloo",
    "byoinnavi",
    "medicalnote",
    "qlife",
    "scuel",
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
    return classify_source(url) != "job"


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

    if area:
        queries.append(f"{name} {area} 病院")
        queries.append(f"{name} {area} 病院 住所")
    else:
        queries.append(f"{name} 病院")
        queries.append(f"{name} 病院 住所")

    # site系は2本だけに絞る
    queries.append(f"site:byoinnavi.jp {name}")
    queries.append(f"site:caloo.jp {name}")

    # 重複除去
    deduped = []
    seen = set()

    for q in queries:
        if q in seen:
            continue
        seen.add(q)
        deduped.append(q)

    return deduped[:4]


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

    for kw in ["病院", "医院", "クリニック", "医療法人", "アクセス", "入院"]:
        if kw in title:
            score += 5

    return score


def search_hospital_candidate_urls(name, area=""):
    queries = build_queries(name, area)
    results = []

    for query in queries:
        items = search_web(query)

        for item in items[:5]:
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

    best_by_url = {}

    for item in results:
        url = item["url"]

        if url not in best_by_url or item["score"] > best_by_url[url]["score"]:
            best_by_url[url] = item

    deduped = list(best_by_url.values())
    deduped.sort(key=lambda x: x.get("score", 0), reverse=True)

    return deduped[:8]
