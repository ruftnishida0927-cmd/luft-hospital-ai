# -*- coding: utf-8 -*-
from urllib.parse import urlparse

from search_provider import search_web


def classify_source(url):
    host = urlparse(url).netloc.lower()

    if "wikipedia.org" in host:
        return "wiki"

    official_like = [
        ".or.jp",
        ".jp",
        ".hospital",
        ".clinic"
    ]

    portal_keywords = [
        "caloo",
        "byoinnavi",
        "medicalnote",
        "qlife",
        "scuel",
        "navitime",
        "fdoc",
        "epark"
    ]

    ng_keywords = [
        "indeed",
        "townwork",
        "rikunabi",
        "job-medley",
        "staffservice",
        "manpower",
        "hatarako",
        "baitoru",
        "en-gage",
        "career",
        "求人"
    ]

    for ng in ng_keywords:
        if ng in host:
            return "job"

    for kw in portal_keywords:
        if kw in host:
            return "portal"

    for suffix in official_like:
        if host.endswith(suffix):
            return "official"

    return "other"


def is_hospital_candidate(url):
    source = classify_source(url)
    return source in ["official", "portal", "wiki"]


def search_hospital_candidate_urls(name):
    queries = [
        f"{name} 病院 公式",
        f"{name} 病院 住所",
        f"{name} 病院 アクセス",
        f"{name} 医療法人",
        f"{name} 病院 所在地"
    ]

    results = []

    for query in queries:
        items = search_web(query)

        for item in items:
            url = item["url"]

            if not is_hospital_candidate(url):
                continue

            item["source"] = classify_source(url)
            results.append(item)

    deduped = []
    seen = set()

    for item in results:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        deduped.append(item)

    return deduped[:10]
