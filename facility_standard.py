# facility_standard.py
# -*- coding: utf-8 -*-

from search_provider import fetch_page_text
from extractors import extract_facility_lines, split_facility_items


def analyze_facility_standards(url_rows: list[dict], debug: bool = False) -> dict:
    """
    facilityカテゴリのURL群から、施設基準/加算の記載を拾う
    勝手な補完はしない
    """
    page_results = []
    all_lines = []

    for row in url_rows[:8]:
        url = row.get("url", "")
        text = fetch_page_text(url, timeout=15, max_chars=50000)
        lines = extract_facility_lines(text)

        page_results.append({
            "url": url,
            "matched_line_count": len(lines),
            "matched_lines": lines[:30],
        })

        all_lines.extend(lines)

    uniq = []
    seen = set()
    for line in all_lines:
        if line not in seen:
            seen.add(line)
            uniq.append(line)

    split_items = split_facility_items(uniq)

    status = "ok" if uniq else "not_found"

    return {
        "status": status,
        "confirmed_lines": uniq[:80],
        "basic_rates": split_items.get("basic_rates", []),
        "additions": split_items.get("additions", []),
        "other_items": split_items.get("other_items", []),
        "debug_pages": page_results if debug else [],
    }
