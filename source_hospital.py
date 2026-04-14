# -*- coding: utf-8 -*-
from urllib.parse import urlparse

from search_provider import search_web


def classify_source(url):
    host = urlparse(url).netloc.lower()

    if "wikipedia.org" in host:
        return "wiki"

    portal_keywords = [
        "caloo", "byoinnavi", "medicalnote", "qlife",
        "scuel", "fdoc", "epark", "navitime"
    ]
    for kw in portal_keywords:
        if kw in host:
            return "portal"

    ng_keywords = [
        "indeed", "townwork", "rikunabi", "job-medley",
        "staffservice", "manpower", "hatarako", "baitoru",
        "en-gage", "career"
    ]
    for ng in ng_keywords:
        if ng in host:
            return "job"

    # .or.jp / .jp は公式候補として広めに扱う
    if host.endswith(".or.jp") or host.endswith(".jp"):
        return "official"

    return "other"


def is_hospital_candidate(url):
    source = classify_source(url)

    # 厳しくしすぎると全部死ぬので、job以外は通す
    return source != "job"


def search_hospital_candidate_urls(name, area=""):
    queries = []

    # 地域指定あり
    if area:
        queries += [
            f"{name} {area} 病院",
            f"{name} {area} 病院 住所",
            f"{name} {area} 病院 アクセス",
            f"{name} {area} 医療法人",
            f"{name} {area} 病院 所在地",
            f"{name} {area} クリニック"
        ]

    # 地域指定なし
    queries += [
        f"{name} 病院",
        f"{name} 病院 住所",
        f"{name} 病院 アクセス",
        f"{name} 医療法人",
        f"{name} 病院 所在地",
        f"{name} クリニック"
    ]

    results = []

    for query in queries:
        items = search_web(query)

        for item in items:
            url = item.get("url", "")
            if not url:
                continue

            if not is_hospital_candidate(url):
                continue

            results.append({
                "title": item.get("title", ""),
                "url": url,
                "snippet": item.get("snippet", ""),
                "source": classify_source(url)
            })

    # 重複除去
    deduped = []
    seen = set()

    for item in results:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        deduped.append(item)

    return deduped[:15]
