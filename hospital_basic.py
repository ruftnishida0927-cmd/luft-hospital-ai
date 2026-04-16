# hospital_basic.py
# -*- coding: utf-8 -*-

import re
from collections import defaultdict

from source_hospital import collect_hospital_candidate_urls
from search_provider import fetch_page_text
from extractors import extract_basic_facts


def _normalize_name(name: str) -> str:
    if not name:
        return ""
    name = re.sub(r"\s+", "", name)
    name = name.replace("医療法人", "")
    name = name.replace("一般財団法人", "")
    name = name.replace("社会医療法人", "")
    name = name.replace("医療法人社団", "")
    return name


def _safe_contains_name(text: str, hospital_name: str) -> bool:
    if not text or not hospital_name:
        return False

    norm_text = _normalize_name(text)
    norm_name = _normalize_name(hospital_name)

    return norm_name in norm_text


def _source_score(source_type: str) -> int:
    table = {
        "official": 5,
        "public": 4,
        "medical-db": 3,
        "other": 1,
        "unknown": 0,
    }
    return table.get(source_type, 0)


def _fact_score(facts: dict) -> int:
    score = 0

    if facts.get("address") and facts["address"] != "不明":
        score += 4
    if facts.get("region") and facts["region"] != "不明":
        score += 2
    if facts.get("nearest_station") and facts["nearest_station"] != "不明":
        score += 2
    if facts.get("bed_count") and facts["bed_count"] != "不明":
        score += 2
    if facts.get("departments") and facts["departments"] != "不明":
        score += 2

    return score


def _title_score(title: str, hospital_name: str) -> int:
    if _safe_contains_name(title, hospital_name):
        return 6
    return 0


def _body_name_score(text: str, hospital_name: str) -> int:
    if not text:
        return 0

    score = 0
    if _safe_contains_name(text[:3000], hospital_name):
        score += 4
    if _safe_contains_name(text[:1000], hospital_name):
        score += 2
    return score


def _build_candidate_record(row: dict, hospital_name: str, debug: bool = False) -> dict:
    url = row.get("url", "")
    title = row.get("title", "")
    source_type = row.get("source_type", "unknown")

    text = fetch_page_text(url, timeout=8, max_chars=22000)
    facts = extract_basic_facts(text, title=title, url=url)

    score = 0
    score += _source_score(source_type)
    score += _title_score(title, hospital_name)
    score += _body_name_score(text, hospital_name)
    score += _fact_score(facts)

    # 「病院」文字がまったくなく、かつ本文も極端に薄い場合は減点
    if "病院" not in title and "病院" not in text[:2000]:
        score -= 3

    return {
        "title": title,
        "url": url,
        "query": row.get("query", ""),
        "provider": row.get("provider", ""),
        "source_type": source_type,
        "domain": row.get("domain", ""),
        "score": score,
        "facts": facts,
        "text_preview": text[:800] if debug else "",
    }


def _merge_best_candidate(candidates: list, hospital_name: str) -> dict:
    """
    URL単位の候補から最良の1件を選ぶ。
    ここでは大胆な統合はせず、まず誤判定を減らすため保守的に選ぶ。
    """
    if not candidates:
        return {
            "status": "not_found",
            "selected": None,
            "candidates": [],
        }

    sorted_rows = sorted(candidates, key=lambda x: x["score"], reverse=True)
    best = sorted_rows[0]

    # 2位との差が小さい場合は曖昧扱い
    second_score = sorted_rows[1]["score"] if len(sorted_rows) >= 2 else -999
    diff = best["score"] - second_score

    # 最低限の信頼条件
    has_name = (
        _safe_contains_name(best.get("title", ""), hospital_name) or
        _safe_contains_name(best.get("text_preview", ""), hospital_name) or
        _safe_contains_name(str(best.get("facts", {}).get("name_candidate", "")), hospital_name)
    )
    has_address = best.get("facts", {}).get("address", "不明") != "不明"

    if best["score"] < 10:
        status = "low_confidence"
    elif diff <= 1 and not has_address:
        status = "ambiguous"
    elif not has_name and not has_address:
        status = "low_confidence"
    else:
        status = "ok"

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
    }


def identify_hospital_basic(hospital_name: str, debug: bool = False) -> dict:
    """
    ステップ:
    ① 候補URL収集
    ② 本文取得
    ③ 基本情報抽出
    ④ スコアリング
    ⑤ 病院特定
    """
    url_rows = collect_hospital_candidate_urls(hospital_name, debug=debug, max_urls=10)

    if not url_rows:
        return {
            "status": "not_found",
            "selected": None,
            "candidates": [],
            "debug_info": {
                "message": "候補URLが取得できませんでした。"
            } if debug else {}
        }

    candidate_rows = []
    errors = []

    for row in url_rows[:8]:
        try:
            rec = _build_candidate_record(row, hospital_name, debug=debug)
            candidate_rows.append(rec)
        except Exception as e:
            errors.append({
                "url": row.get("url", ""),
                "error": str(e),
            })

    merged = _merge_best_candidate(candidate_rows, hospital_name)

    if debug:
        merged["debug_info"] = {
            "collected_url_count": len(url_rows),
            "scored_candidate_count": len(candidate_rows),
            "errors": errors,
        }

    return merged
