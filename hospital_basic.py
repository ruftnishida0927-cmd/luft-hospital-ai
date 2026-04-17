# hospital_basic.py
# -*- coding: utf-8 -*-

from search_provider import fetch_page_text
from source_hospital import discover_related_pages, classify_source
from extractors import (
    extract_basic_facts,
    extract_group_candidates,
)
from facility_standard import analyze_facility_standards
from staff_contact import analyze_staff_contacts


def _pick_best_value(values: list[dict], key: str) -> dict:
    """
    values: [{"value": ..., "source_type": ..., "url": ..., "update_dates": [...]}]
    優先順位:
    1. 値が不明でない
    2. 同じ値の出現数
    3. public > official > other
    """
    filtered = [v for v in values if v.get("value") and v.get("value") != "不明"]
    if not filtered:
        return {
            "adopted_value": "不明",
            "consistency": "不明",
            "evidence": [],
        }

    freq = {}
    for row in filtered:
        val = row["value"]
        freq[val] = freq.get(val, 0) + 1

    def source_rank(source_type: str) -> int:
        if source_type == "public":
            return 3
        if source_type == "official":
            return 2
        return 1

    sorted_rows = sorted(
        filtered,
        key=lambda x: (
            freq.get(x["value"], 0),
            source_rank(x.get("source_type", "")),
            len(x.get("update_dates", [])),
        ),
        reverse=True,
    )

    adopted = sorted_rows[0]["value"]
    unique_values = list({x["value"] for x in filtered})

    if len(unique_values) == 1:
        consistency = "一致"
    elif freq.get(adopted, 0) >= 2:
        consistency = "多数一致"
    else:
        consistency = "一部不一致"

    return {
        "adopted_value": adopted,
        "consistency": consistency,
        "evidence": filtered[:10],
    }


def analyze_hospital_from_url(
    hospital_name: str,
    main_url: str,
    public_urls: list[str] | None = None,
    recruit_urls: list[str] | None = None,
    group_urls: list[str] | None = None,
    extra_official_urls: list[str] | None = None,
    debug: bool = False,
) -> dict:
    public_urls = public_urls or []
    recruit_urls = recruit_urls or []
    group_urls = group_urls or []
    extra_official_urls = extra_official_urls or []

    related = discover_related_pages(
        main_url=main_url,
        public_urls=public_urls,
        recruit_urls=recruit_urls,
        group_urls=group_urls,
        extra_official_urls=extra_official_urls,
        max_pages=40,
    )

    if related.get("status") != "ok":
        return {
            "status": "error",
            "hospital_name": hospital_name,
            "main_url": main_url,
            "error": related.get("error", "関連ページ探索に失敗しました。"),
            "debug_info": related if debug else {},
        }

    categories = related.get("categories", {})
    basic_pages = categories.get("basic", [])
    facility_pages = categories.get("facility", [])
    recruit_pages = categories.get("recruit", [])
    group_pages = categories.get("group", [])
    contact_pages = categories.get("contact", [])
    public_pages = categories.get("public", [])

    # 基本情報比較
    basic_candidates = []
    for row in ([{"url": main_url, "label": "main", "source_type": classify_source(main_url)}] + basic_pages + public_pages)[:12]:
        url = row.get("url", "")
        text = fetch_page_text(url, timeout=15, max_chars=70000)
        facts = extract_basic_facts(text, title=row.get("label", ""), url=url)

        basic_candidates.append({
            "url": url,
            "source_type": row.get("source_type", classify_source(url)),
            "address": facts.get("address", "不明"),
            "region": facts.get("region", "不明"),
            "nearest_station": facts.get("nearest_station", "不明"),
            "bed_count": facts.get("bed_count", "不明"),
            "departments": facts.get("departments", "不明"),
            "hospital_type": facts.get("hospital_type", "不明"),
            "function_hints": facts.get("function_hints", []),
            "update_dates": facts.get("update_dates", []),
        })

    adopted_address = _pick_best_value(
        [{"value": x["address"], "source_type": x["source_type"], "url": x["url"], "update_dates": x["update_dates"]} for x in basic_candidates],
        "address",
    )
    adopted_region = _pick_best_value(
        [{"value": x["region"], "source_type": x["source_type"], "url": x["url"], "update_dates": x["update_dates"]} for x in basic_candidates],
        "region",
    )
    adopted_station = _pick_best_value(
        [{"value": x["nearest_station"], "source_type": x["source_type"], "url": x["url"], "update_dates": x["update_dates"]} for x in basic_candidates],
        "nearest_station",
    )
    adopted_bed_count = _pick_best_value(
        [{"value": x["bed_count"], "source_type": x["source_type"], "url": x["url"], "update_dates": x["update_dates"]} for x in basic_candidates],
        "bed_count",
    )
    adopted_departments = _pick_best_value(
        [{"value": x["departments"], "source_type": x["source_type"], "url": x["url"], "update_dates": x["update_dates"]} for x in basic_candidates],
        "departments",
    )
    adopted_hospital_type = _pick_best_value(
        [{"value": x["hospital_type"], "source_type": x["source_type"], "url": x["url"], "update_dates": x["update_dates"]} for x in basic_candidates],
        "hospital_type",
    )

    # 病院機能ヒント
    function_hints = []
    for row in basic_candidates:
        for hint in row.get("function_hints", []):
            if hint not in function_hints:
                function_hints.append(hint)

    # 施設基準
    facility_result = analyze_facility_standards(
        official_rows=facility_pages + basic_pages,
        public_rows=public_pages,
        debug=debug,
    )

    # 求人窓口
    staff_result = analyze_staff_contacts(
        official_recruit_rows=recruit_pages + contact_pages,
        external_recruit_rows=[{"url": u} for u in recruit_urls],
        debug=debug,
    )

    # グループ情報
    group_candidates = []
    group_source_urls = []
    target_group_pages = group_pages[:6] if group_pages else basic_pages[:3]

    for row in target_group_pages:
        url = row.get("url", "")
        text = fetch_page_text(url, timeout=15, max_chars=70000)
        group_source_urls.append(url)
        group_candidates.extend(extract_group_candidates(text))

    uniq_group = []
    seen_group = set()
    for g in group_candidates:
        if g not in seen_group:
            seen_group.add(g)
            uniq_group.append(g)

    status = "ok"
    if adopted_address["adopted_value"] == "不明" and adopted_region["adopted_value"] == "不明":
        status = "low_confidence"

    return {
        "status": status,
        "hospital_name": hospital_name,
        "main_url": main_url,
        "source_type": classify_source(main_url),
        "basic_info": {
            "address": adopted_address,
            "region": adopted_region,
            "nearest_station": adopted_station,
            "bed_count": adopted_bed_count,
            "departments": adopted_departments,
            "hospital_type": adopted_hospital_type,
            "function_hints": function_hints,
            "basic_candidates": basic_candidates if debug else [],
        },
        "facility_info": facility_result,
        "staff_contact_info": staff_result,
        "group_info": {
            "status": "ok" if uniq_group else "not_found",
            "consistency": "候補抽出",
            "candidates": uniq_group[:50],
            "source_urls": group_source_urls[:10],
        },
        "discovered_pages": categories,
        "debug_info": related if debug else {},
    }
