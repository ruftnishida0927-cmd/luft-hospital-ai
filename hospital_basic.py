# -*- coding: utf-8 -*-
from extractors import (
    extract_prefecture,
    extract_departments,
    extract_bed_count,
    extract_station,
    extract_hospital_type_flags
)
from search_provider import search_web, fetch_page_text


def _is_likely_official_or_profile_url(url: str) -> bool:
    u = url.lower()

    ng_keywords = [
        "indeed", "townwork", "rikunabi", "job-medley",
        "staffservice", "manpower", "hatarako", "baitoru",
        "求人", "career", "mc-nurse", "en-gage"
    ]

    for ng in ng_keywords:
        if ng in u:
            return False

    return True


def build_info(text, name, source_url):
    flags = extract_hospital_type_flags(text)

    return {
        "病院名": name,
        "病床数": extract_bed_count(text) or "不明",
        "病院種別": "一般病院",
        "地域": extract_prefecture(text),
        "最寄駅": extract_station(text),
        "急性期": flags["急性期"],
        "回復期": flags["回復期"],
        "療養": flags["療養"],
        "診療科": extract_departments(text) or ["調査中"],
        "URL": source_url
    }


def get_hospital_basic_info(name):
    queries = [
        f"{name} 病院 公式",
        f"{name} 病院 法人",
        f"{name} 病院 住所",
        f"{name} 病院 最寄駅"
    ]

    candidate_urls = []

    for query in queries:
        results = search_web(query)

        for r in results:
            url = r["url"]

            if not _is_likely_official_or_profile_url(url):
                continue

            candidate_urls.append(url)

    # 重複除去
    deduped_urls = []
    seen = set()

    for u in candidate_urls:
        if u in seen:
            continue
        seen.add(u)
        deduped_urls.append(u)

    candidates = []

    for url in deduped_urls[:5]:
        text = fetch_page_text(url)

        if not text:
            continue

        info = build_info(text, name, url)
        candidates.append(info)

    if not candidates:
        return [{
            "病院名": name,
            "病床数": "不明",
            "病院種別": "不明",
            "地域": "不明",
            "最寄駅": "不明",
            "急性期": False,
            "回復期": False,
            "療養": False,
            "診療科": ["調査中"],
            "URL": ""
        }]

    return candidates
