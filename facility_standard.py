# facility_standard.py
# -*- coding: utf-8 -*-

from search_provider import fetch_page_text
from extractors import extract_facility_lines, split_facility_items, extract_update_date_candidates


def _uniq_keep_order(items):
    seen = set()
    out = []
    for x in items:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def analyze_facility_standards(official_rows: list[dict], public_rows: list[dict], debug: bool = False) -> dict:
    """
    公式系URLと公的URLを分けて読み、
    最終的に整合性を見て採用結果を作る
    """
    official_page_results = []
    public_page_results = []

    official_lines = []
    public_lines = []

    for row in official_rows[:8]:
        url = row.get("url", "")
        text = fetch_page_text(url, timeout=15, max_chars=70000)
        lines = extract_facility_lines(text)
        dates = extract_update_date_candidates(text)

        official_page_results.append({
            "url": url,
            "matched_line_count": len(lines),
            "matched_lines": lines[:30],
            "update_dates": dates[:5],
        })
        official_lines.extend(lines)

    for row in public_rows[:8]:
        url = row.get("url", "")
        text = fetch_page_text(url, timeout=15, max_chars=70000)
        lines = extract_facility_lines(text)
        dates = extract_update_date_candidates(text)

        public_page_results.append({
            "url": url,
            "matched_line_count": len(lines),
            "matched_lines": lines[:30],
            "update_dates": dates[:5],
        })
        public_lines.extend(lines)

    official_lines = _uniq_keep_order(official_lines)
    public_lines = _uniq_keep_order(public_lines)

    official_split = split_facility_items(official_lines)
    public_split = split_facility_items(public_lines)

    # 採用結果の基本方針:
    # 公的ソースがあればそれを優先
    # なければ公式ソース
    if public_lines:
        adopted_source = "public"
        adopted_split = public_split
        consistency = "一致" if official_lines and set(public_lines).intersection(set(official_lines)) else "公的優先"
    elif official_lines:
        adopted_source = "official"
        adopted_split = official_split
        consistency = "HP記載のみ"
    else:
        adopted_source = "none"
        adopted_split = {"basic_rates": [], "additions": [], "other_items": []}
        consistency = "不明"

    return {
        "status": "ok" if (official_lines or public_lines) else "not_found",
        "adopted_source": adopted_source,
        "consistency": consistency,
        "official_confirmed_lines": official_lines[:80],
        "public_confirmed_lines": public_lines[:80],
        "adopted_basic_rates": adopted_split.get("basic_rates", []),
        "adopted_additions": adopted_split.get("additions", []),
        "adopted_other_items": adopted_split.get("other_items", []),
        "debug_official_pages": official_page_results if debug else [],
        "debug_public_pages": public_page_results if debug else [],
    }
