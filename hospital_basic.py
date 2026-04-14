# -*- coding: utf-8 -*-
import re

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


def score_candidate(info, area=""):
    score = 0

    address = info.get("住所", "")
    region = info.get("地域", "不明")
    station = info.get("最寄駅", "不明")
    beds = info.get("病床数", "不明")
    deps = info.get("診療科", [])
    source = info.get("取得元", "")

    if address:
        score += 40
    if region not in ["", "不明", None]:
        score += 20
    if station not in ["", "不明", None]:
        score += 10
    if beds not in ["", "不明", None]:
        score += 10
    if deps and deps != ["調査中"]:
        score += 10

    if source == "official":
        score += 15
    elif source == "portal":
        score += 10
    elif source == "wiki":
        score += 5

    if area:
        if area in address or area == region or area in station:
            score += 30
        else:
            score -= 10

    if score < 0:
        score = 0

    return score


def is_valid_candidate(info):
    address = info.get("住所", "")
    region = info.get("地域", "不明")
    station = info.get("最寄駅", "不明")
    beds = info.get("病床数", "不明")
    deps = info.get("診療科", ["調査中"])

    if address:
        return True
    if region not in ["", "不明", None]:
        return True
    if station not in ["", "不明", None]:
        return True
    if beds not in ["", "不明", None]:
        return True
    if deps and deps != ["調査中"]:
        return True

    return False


def get_hospital_basic_info_debug(name, area=""):
    debug = {
        "input_name": name,
        "input_area": area,
        "search_results_count": 0,
        "candidate_source_count": 0,
        "page_fetch_success_count": 0,
        "valid_candidate_count": 0,
        "candidate_sources": [],
        "page_details": []
    }

    candidate_sources = search_hospital_candidate_urls(name, area)
    debug["search_results_count"] = len(candidate_sources)
    debug["candidate_source_count"] = len(candidate_sources)
    debug["candidate_sources"] = candidate_sources[:10]

    raw_candidates = []

    for item in candidate_sources[:10]:
        url = item.get("url", "")
        source = item.get("source", "other")
        title = item.get("title", "")

        if not url:
            debug["page_details"].append({
                "url": "",
                "source": source,
                "title": title,
                "fetched": False,
                "text_len": 0,
                "住所": "",
                "地域": "不明",
                "最寄駅": "不明",
                "病床数": "不明",
                "valid": False
            })
            continue

        text = fetch_page_text(url)

        fetched = bool(text)
        if fetched:
            debug["page_fetch_success_count"] += 1

        info = build_info(text if text else "", name, url, source)
        valid = is_valid_candidate(info)

        debug["page_details"].append({
            "url": url,
            "source": source,
            "title": title,
            "fetched": fetched,
            "text_len": len(text) if text else 0,
            "住所": info["住所"],
            "地域": info["地域"],
            "最寄駅": info["最寄駅"],
            "病床数": info["病床数"],
            "valid": valid
        })

        if valid:
            raw_candidates.append(info)

    debug["valid_candidate_count"] = len(raw_candidates)

    if not raw_candidates:
        fallback = [{
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
            "取得元": "",
            "スコア": 0
        }]
        return fallback, debug

    for c in raw_candidates:
        c["スコア"] = score_candidate(c, area)

    raw_candidates.sort(key=lambda x: x["スコア"], reverse=True)

    return raw_candidates, debug


def get_hospital_basic_info(name, area=""):
    candidates, _ = get_hospital_basic_info_debug(name, area)
    return candidates
