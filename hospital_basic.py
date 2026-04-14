# -*- coding: utf-8 -*-
from extractors import (
    extract_prefecture,
    extract_address,
    extract_departments,
    extract_bed_count,
    extract_station,
    extract_hospital_type_flags
)
from source_hospital import search_hospital_candidate_urls
from search_provider import fetch_page_text


def build_info(text, name, url, source):
    flags = extract_hospital_type_flags(text)

    return {
        "病院名": name,
        "病院種別": "一般病院",
        "住所": extract_address(text),
        "地域": extract_prefecture(text),
        "最寄駅": extract_station(text),
        "病床数": extract_bed_count(text) or "不明",
        "急性期": flags["急性期"],
        "回復期": flags["回復期"],
        "療養": flags["療養"],
        "診療科": extract_departments(text) or ["調査中"],
        "URL": url,
        "取得元": source
    }


def score_candidate(info):
    score = 0

    if info.get("住所"):
        score += 50

    if info.get("地域") not in ["", "不明", None]:
        score += 20

    if info.get("最寄駅") not in ["", "不明", None]:
        score += 10

    if info.get("病床数") not in ["", "不明", None]:
        score += 10

    deps = info.get("診療科", [])
    if deps and deps != ["調査中"]:
        score += 10

    source = info.get("取得元", "")
    if source == "official":
        score += 15
    elif source == "portal":
        score += 10
    elif source == "wiki":
        score += 5

    return score


def is_valid_candidate(info):
    # 住所 or 地域がないものは弱すぎる
    if not info.get("住所") and info.get("地域") == "不明":
        return False

    # 住所も駅も病床も診療科も全部ないものは除外
    if (
        not info.get("住所")
        and info.get("最寄駅") == "不明"
        and info.get("病床数") == "不明"
        and info.get("診療科") == ["調査中"]
    ):
        return False

    return True


def dedupe_candidates(candidates):
    deduped = []
    seen = set()

    for c in candidates:
        key = (
            c.get("住所", ""),
            c.get("地域", ""),
            c.get("最寄駅", ""),
            str(c.get("病床数", "")),
            c.get("URL", "")
        )

        if key in seen:
            continue

        seen.add(key)
        deduped.append(c)

    return deduped


def get_hospital_basic_info(name):
    candidate_sources = search_hospital_candidate_urls(name)

    candidates = []

    for item in candidate_sources[:8]:
        url = item["url"]
        source = item.get("source", "other")

        text = fetch_page_text(url)

        if not text:
            continue

        info = build_info(text, name, url, source)

        if is_valid_candidate(info):
            candidates.append(info)

    candidates = dedupe_candidates(candidates)

    if not candidates:
        return [{
            "病院名": name,
            "病院種別": "不明",
            "住所": "",
            "地域": "不明",
            "最寄駅": "不明",
            "病床数": "不明",
            "急性期": False,
            "回復期": False,
            "療養": False,
            "診療科": ["調査中"],
            "URL": "",
            "取得元": ""
        }]

    candidates.sort(key=score_candidate, reverse=True)

    return candidates
