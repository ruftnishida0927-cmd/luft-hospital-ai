# hospital_basic.py
# -*- coding: utf-8 -*-

import re
from collections import Counter

from source_hospital import search_hospital_candidates
from search_provider import fetch_page_text
from extractors import extract_basic_facts, is_generic_ambiguous_hospital_name


def _normalize_name(name: str) -> str:
    if not name:
        return ""
    name = re.sub(r"\s+", "", name)
    for word in ["医療法人", "一般財団法人", "社会医療法人", "医療法人社団"]:
        name = name.replace(word, "")
    return name


def _safe_contains_name(text: str, hospital_name: str) -> bool:
    if not text or not hospital_name:
        return False
    return _normalize_name(hospital_name) in _normalize_name(text)


def _url_score(url: str) -> int:
    if not url:
        return 0

    score = 0
    if "byoinnavi.jp/clinic/" in url:
        score += 12
    if "caloo.jp/hospitals/detail/" in url:
        score += 12
    if "qlife.jp/hospital_detail_" in url:
        score += 12
    if "medicalnote.jp/hospitals/" in url:
        score += 10

    if "freeword?q=" in url:
        score -= 20
    if "/search/all" in url:
        score -= 20
    if "search_hospital_result" in url:
        score -= 20

    return score


def _source_score(source_type: str) -> int:
    table = {
        "official": 12,
        "public": 10,
        "medical-db": 5,
        "other": 1,
        "unknown": 0,
    }
    return table.get(source_type, 0)


def _fact_score(facts: dict) -> int:
    score = 0
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
    return score


def _build_candidate_record(row: dict, hospital_name: str, debug: bool = False) -> dict:
    url = row.get("url", "")
    title = row.get("title", "")
    source_type = row.get("source_type", "unknown")

    text = fetch_page_text(url, timeout=8, max_chars=22000)
    facts = extract_basic_facts(text, title=title, url=url)

    score = 0
    score += _url_score(url)
    score += _source_score(source_type)
    score += 8 if _safe_contains_name(title, hospital_name) else 0
    score += 6 if _safe_contains_name(text[:3000], hospital_name) else 0
    score += _fact_score(facts)

    return {
        "title": title,
        "url": url,
        "query": row.get("query", ""),
        "provider": row.get("provider", ""),
        "source_type": source_type,
        "domain": row.get("domain", ""),
        "score": score,
        "facts": facts,
        "text_preview": text[:1200] if debug else "",
    }


def _pref_consensus(candidates: list) -> dict:
    prefs = []
    for c in candidates[:5]:
        region = c.get("facts", {}).get("region", "不明")
        if region != "不明":
            pref = re.sub(r"(市|区|町|村).*$", "", region)
            prefs.append(pref)

    if not prefs:
        return {"top_pref": "不明", "count": 0, "all": []}

    counter = Counter(prefs)
    top_pref, count = counter.most_common(1)[0]
    return {"top_pref": top_pref, "count": count, "all": prefs}


def _has_strong_name_match(candidate: dict, hospital_name: str) -> bool:
    if _safe_contains_name(candidate.get("title", ""), hospital_name):
        return True
    if _safe_contains_name(candidate.get("text_preview", ""), hospital_name):
        return True
    if _safe_contains_name(candidate.get("facts", {}).get("name_candidate", ""), hospital_name):
        return True
    return False


def identify_hospital_basic(hospital_name: str, debug: bool = False) -> dict:
    collected = search_hospital_candidates(hospital_name, max_urls=10)
    url_rows = collected.get("rows", [])
    query_debug = collected.get("debug", [])

    if not url_rows:
        return {
            "status": "not_found",
            "selected": None,
            "candidates": [],
            "debug_info": {
                "message": "有効な候補URLが取得できませんでした。",
                "query_debug": query_debug,
            } if debug else {}
        }

    candidate_rows = []
    errors = []

    for row in url_rows[:8]:
        try:
            candidate_rows.append(_build_candidate_record(row, hospital_name, debug=debug))
        except Exception as e:
            errors.append({
                "url": row.get("url", ""),
                "error": str(e),
            })

    if not candidate_rows:
        return {
            "status": "not_found",
            "selected": None,
            "candidates": [],
            "debug_info": {
                "message": "候補URLはあったが本文取得・抽出に失敗しました。",
                "query_debug": query_debug,
                "errors": errors,
            } if debug else {}
        }

    sorted_rows = sorted(candidate_rows, key=lambda x: x["score"], reverse=True)
    best = sorted_rows[0]
    second_score = sorted_rows[1]["score"] if len(sorted_rows) >= 2 else -999
    diff = best["score"] - second_score

    has_name = _has_strong_name_match(best, hospital_name)
    has_address = best.get("facts", {}).get("address", "不明") != "不明"
    ambiguous_name = is_generic_ambiguous_hospital_name(hospital_name)
    pref_info = _pref_consensus(sorted_rows)

    status = "ok"
    if best["score"] < 18:
        status = "low_confidence"
    elif ambiguous_name and not has_address:
        status = "ambiguous"
    elif diff <= 2 and not has_address:
        status = "ambiguous"
    elif not has_name and not has_address:
        status = "low_confidence"

    selected = {
        "hospital_name_input": hospital_name,
        "title": best.get("title", ""),
        "url": best.get("url", ""),
        "source_type": best.get("source_type", ""),
        "score": best.get("score", 0),
        "address": best.get("facts", {}).get("address", "不明"),
        "region": best.get("facts", {}).get("region", "不明"),
        "nearest_station": best.get("facts", {}).get("nearest_station", "不明"),
        "bed_count": best.get("facts", {}).get("bed_count", "不明"),
        "departments": best.get("facts", {}).get("departments", "不明"),
        "hospital_type": best.get("facts", {}).get("hospital_type", "不明"),
    }

    return {
        "status": status,
        "selected": selected,
        "candidates": sorted_rows[:8],
        "consensus": pref_info,
        "debug_info": {
            "message": "有効候補URLベースで評価しました。",
            "query_debug": query_debug,
            "errors": errors,
        } if debug else {},
    }
