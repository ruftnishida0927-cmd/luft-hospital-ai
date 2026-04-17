# hospital_basic.py
# -*- coding: utf-8 -*-

from search_provider import fetch_page_text
from source_hospital import discover_related_pages, classify_source
from extractors import extract_basic_facts, extract_group_candidates
from facility_standard import analyze_facility_standards
from staff_contact import analyze_staff_contacts


def analyze_hospital_from_url(
    hospital_name: str,
    main_url: str,
    recruit_url: str = "",
    debug: bool = False,
) -> dict:
    """
    URL起点の総合解析
    """
    main_text = fetch_page_text(main_url, timeout=15, max_chars=50000)
    basic = extract_basic_facts(main_text, title=hospital_name, url=main_url)

    extra_urls = [recruit_url] if recruit_url else []
    related = discover_related_pages(main_url, extra_urls=extra_urls, max_pages=25)

    categories = related.get("categories", {})
    basic_pages = categories.get("basic", [])
    facility_pages = categories.get("facility", [])
    recruit_pages = categories.get("recruit", [])
    group_pages = categories.get("group", [])
    contact_pages = categories.get("contact", [])

    # basic情報の補強: basicページも読む
    for row in basic_pages[:5]:
        text = fetch_page_text(row.get("url", ""), timeout=15, max_chars=50000)
        add = extract_basic_facts(text, title=row.get("label", ""), url=row.get("url", ""))

        if basic.get("address") == "不明" and add.get("address") != "不明":
            basic["address"] = add["address"]
            basic["region"] = add["region"]

        if basic.get("nearest_station") == "不明" and add.get("nearest_station") != "不明":
            basic["nearest_station"] = add["nearest_station"]

        if basic.get("bed_count") == "不明" and add.get("bed_count") != "不明":
            basic["bed_count"] = add["bed_count"]

        if basic.get("departments") == "不明" and add.get("departments") != "不明":
            basic["departments"] = add["departments"]

        if basic.get("hospital_type") == "不明" and add.get("hospital_type") != "不明":
            basic["hospital_type"] = add["hospital_type"]

        for hint in add.get("function_hints", []):
            if hint not in basic["function_hints"]:
                basic["function_hints"].append(hint)

    # グループ情報候補
    group_candidates = []
    group_source_urls = []

    group_target_pages = group_pages[:5]
    if not group_target_pages:
        group_target_pages = basic_pages[:3]

    for row in group_target_pages:
        url = row.get("url", "")
        text = fetch_page_text(url, timeout=15, max_chars=50000)
        group_source_urls.append(url)
        group_candidates.extend(extract_group_candidates(text))

    # 重複除去
    uniq_group = []
    seen_group = set()
    for g in group_candidates:
        if g not in seen_group:
            seen_group.add(g)
            uniq_group.append(g)

    # 施設基準
    facility_result = analyze_facility_standards(facility_pages + basic_pages, debug=debug)

    # 求人窓口
    staff_result = analyze_staff_contacts(recruit_pages + contact_pages, debug=debug)

    # 基本ステータス
    status = "ok"
    if basic.get("address") == "不明" and basic.get("region") == "不明":
        status = "low_confidence"

    return {
        "status": status,
        "hospital_name": hospital_name,
        "main_url": main_url,
        "source_type": classify_source(main_url),
        "basic_info": {
            "address": basic.get("address", "不明"),
            "region": basic.get("region", "不明"),
            "nearest_station": basic.get("nearest_station", "不明"),
            "bed_count": basic.get("bed_count", "不明"),
            "departments": basic.get("departments", "不明"),
            "hospital_type": basic.get("hospital_type", "不明"),
            "function_hints": basic.get("function_hints", []),
        },
        "group_info": {
            "status": "ok" if uniq_group else "not_found",
            "candidates": uniq_group[:50],
            "source_urls": group_source_urls[:10],
        },
        "facility_info": facility_result,
        "staff_contact_info": staff_result,
        "discovered_pages": categories,
        "debug_info": related if debug else {},
    }
