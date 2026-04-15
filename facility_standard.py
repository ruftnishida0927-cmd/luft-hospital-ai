# -*- coding: utf-8 -*-
import re
from search_provider import search_web, fetch_page_text


BASE_STANDARD_PATTERNS = [
    ("急性期一般入院料1", [r"急性期一般入院料1"]),
    ("急性期一般入院料2", [r"急性期一般入院料2"]),
    ("急性期一般入院料3", [r"急性期一般入院料3"]),
    ("急性期一般入院料4", [r"急性期一般入院料4"]),
    ("急性期一般入院料5", [r"急性期一般入院料5"]),
    ("急性期一般入院料6", [r"急性期一般入院料6"]),
    ("地域一般入院料1", [r"地域一般入院料1"]),
    ("地域一般入院料2", [r"地域一般入院料2"]),
    ("地域一般入院料3", [r"地域一般入院料3"]),
    ("障害者施設等入院基本料", [r"障害者施設等入院基本料"]),
    ("療養病棟入院基本料", [r"療養病棟入院基本料"]),
    ("地域包括ケア病棟入院料", [r"地域包括ケア病棟入院料"]),
    ("回復期リハビリテーション病棟入院料", [r"回復期リハビリテーション病棟入院料"]),
]

ADDITIONAL_STANDARD_PATTERNS = [
    ("看護補助体制加算", [r"看護補助体制加算"]),
    ("急性期看護補助体制加算", [r"急性期看護補助体制加算"]),
    ("夜間看護補助加算", [r"夜間看護補助加算"]),
    ("看護補助加算", [r"看護補助加算"]),
    ("看護補助加算1", [r"看護補助加算1"]),
    ("看護補助加算2", [r"看護補助加算2"]),
    ("医師事務作業補助体制加算", [r"医師事務作業補助体制加算"]),
    ("診療録管理体制加算", [r"診療録管理体制加算"]),
    ("感染対策向上加算", [r"感染対策向上加算"]),
    ("医療安全対策加算", [r"医療安全対策加算"]),
    ("入退院支援加算", [r"入退院支援加算"]),
    ("データ提出加算", [r"データ提出加算"]),
    ("せん妄ハイリスク患者ケア加算", [r"せん妄ハイリスク患者ケア加算"]),
    ("認知症ケア加算", [r"認知症ケア加算"]),
    ("栄養サポートチーム加算", [r"栄養サポートチーム加算"]),
    ("褥瘡ハイリスク患者ケア加算", [r"褥瘡ハイリスク患者ケア加算"]),
]

MISSING_BY_BASE = {
    "急性期": [
        ("急性期看護補助体制加算", 0),
        ("夜間看護補助加算", 0),
        ("医師事務作業補助体制加算", 0),
        ("診療録管理体制加算", 0),
        ("入退院支援加算", 0),
        ("データ提出加算", 0),
    ],
    "障害者": [
        ("看護補助加算", 0),
        ("看護補助加算1", 0),
        ("看護補助加算2", 0),
        ("医師事務作業補助体制加算", 0),
        ("診療録管理体制加算", 0),
    ],
    "地域一般": [
        ("看護補助体制加算", 0),
        ("医師事務作業補助体制加算", 0),
        ("診療録管理体制加算", 0),
    ],
    "療養": [
        ("看護補助加算", 0),
        ("認知症ケア加算", 0),
        ("褥瘡ハイリスク患者ケア加算", 0),
    ],
    "回復期": [
        ("入退院支援加算", 0),
        ("栄養サポートチーム加算", 0),
        ("認知症ケア加算", 0),
    ],
    "包括ケア": [
        ("入退院支援加算", 0),
        ("認知症ケア加算", 0),
        ("医療安全対策加算", 0),
    ],
    "不明": []
}


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text)


def _is_likely_facility_url(url: str) -> bool:
    u = url.lower()
    ng_keywords = ["indeed", "townwork", "rikunabi", "job-medley", "求人"]
    return not any(ng in u for ng in ng_keywords)


# ★軽量化済みクエリ
def _collect_candidate_urls(hospital_name: str, area: str = "", hospital_info: dict | None = None):
    queries = [
        f"{hospital_name} {area} 施設基準",
        f"{hospital_name} 入院基本料",
        f"{hospital_name} 厚生局 届出",
        f"{hospital_name} 施設基準 PDF"
    ]

    results = []
    for query in queries:
        items = search_web(query)
        for item in items:
            url = item.get("url", "")
            if not url or not _is_likely_facility_url(url):
                continue
            results.append(item)

    seen = set()
    deduped = []
    for item in results:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        deduped.append(item)

    return deduped[:8]  # ★最大8件


def _extract_base_standard(text: str):
    norm = _normalize_text(text)
    for label, patterns in BASE_STANDARD_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, norm):
                return label
    return None


def _extract_additional_standards(text: str):
    norm = _normalize_text(text)
    found = []
    for label, patterns in ADDITIONAL_STANDARD_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, norm):
                found.append(label)
                break
    return list(set(found))


def get_facility_standard_debug(hospital_name, area="", hospital_info=None):
    urls = _collect_candidate_urls(hospital_name, area, hospital_info)

    best_score = 0
    acquired = []

    debug = {
        "candidate_url_count": len(urls),
        "page_details": []
    }

    for item in urls[:5]:  # ★最大5ページ
        url = item["url"]
        text = fetch_page_text(url)

        if not text:
            continue

        base = _extract_base_standard(text)
        adds = _extract_additional_standards(text)

        score = len(adds)
        if base:
            score += 5

        if len(debug["page_details"]) < 5:
            debug["page_details"].append({
                "url": url,
                "base": base,
                "adds": adds,
                "score": score
            })

        if score > best_score:
            best_score = score
            acquired = ([base] if base else []) + adds

    return acquired, [], debug


def get_facility_standard(hospital_name, area="", hospital_info=None):
    acquired, missing, _ = get_facility_standard_debug(hospital_name, area, hospital_info)
    return acquired, missing
