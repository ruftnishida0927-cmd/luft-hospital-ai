# hospital_basic.py
# -*- coding: utf-8 -*-

import re

from source_hospital import search_hospital_candidates
from search_provider import fetch_page_text
from extractors import extract_basic_facts


def analyze_candidate(candidate: dict, hospital_name: str, debug: bool = False) -> dict:
    url = candidate.get("url", "")
    title = candidate.get("title", "")
    source_type = candidate.get("source_type", "unknown")

    text = fetch_page_text(url, timeout=8, max_chars=22000)
    facts = extract_basic_facts(text, title=title, url=url)

    score = 0
    score += candidate.get("internal_score", 0)

    if facts.get("address") != "不明":
        score += 8
    if facts.get("region") != "不明":
        score += 4
    if facts.get("nearest_station") != "不明":
        score += 2
    if facts.get("bed_count") != "不明":
        score += 3
    if facts.get("departments") != "不明":
        score += 2

    if "病院" not in title and "病院" not in text[:2000]:
        score -= 3

    return {
        "hospital_name_input": hospital_name,
        "title": title,
        "url": url,
        "source_type": source_type,
        "score": score,
        "address": facts.get("address", "不明"),
        "region": facts.get("region", "不明"),
        "nearest_station": facts.get("nearest_station", "不明"),
        "bed_count": facts.get("bed_count", "不明"),
        "departments": facts.get("departments", "不明"),
        "hospital_type": facts.get("hospital_type", "不明"),
        "debug_text_preview": text[:1200] if debug else "",
    }


def search_hospital_phase(hospital_name: str, prefecture: str = "", debug: bool = False) -> dict:
    collected = search_hospital_candidates(hospital_name, prefecture=prefecture, max_urls=10)
    rows = collected.get("rows", [])
    query_debug = collected.get("debug", [])

    return {
        "status": "ok" if rows else "not_found",
        "candidates": rows,
        "debug_info": {
            "message": "候補URL検索結果です。",
            "query_debug": query_debug,
        } if debug else {},
    }


def identify_from_selected_candidate(hospital_name: str, selected_url: str, prefecture: str = "", debug: bool = False) -> dict:
    collected = search_hospital_candidates(hospital_name, prefecture=prefecture, max_urls=10)
    rows = collected.get("rows", [])
    query_debug = collected.get("debug", [])

    target = None
    for row in rows:
        if row.get("url") == selected_url:
            target = row
            break

    if not target:
        return {
            "status": "not_found",
            "selected": None,
            "candidates": [],
            "debug_info": {
                "message": "選択された候補URLが現在の候補一覧に存在しません。",
                "query_debug": query_debug,
            } if debug else {},
        }

    analyzed = analyze_candidate(target, hospital_name, debug=debug)

    status = "ok" if analyzed.get("address") != "不明" or analyzed.get("region") != "不明" else "low_confidence"

    return {
        "status": status,
        "selected": analyzed,
        "candidates": [analyzed],
        "debug_info": {
            "message": "選択候補を解析しました。",
            "query_debug": query_debug,
        } if debug else {},
    }
