# -*- coding: utf-8 -*-
from search_provider import search_web, fetch_page_text


STANDARD_KEYWORDS = [
    "急性期一般入院料1",
    "急性期一般入院料2",
    "急性期一般入院料3",
    "急性期一般入院料4",
    "急性期一般入院料5",
    "急性期一般入院料6",
    "地域一般入院料1",
    "地域一般入院料2",
    "地域一般入院料3",
    "地域包括ケア病棟入院料",
    "回復期リハビリテーション病棟入院料",
    "療養病棟入院基本料",
    "看護補助体制加算",
    "急性期看護補助体制加算",
    "夜間看護補助加算",
    "看護補助加算",
    "医師事務作業補助体制加算",
    "診療録管理体制加算",
    "感染対策向上加算",
    "医療安全対策加算",
    "入退院支援加算",
    "データ提出加算",
    "せん妄ハイリスク患者ケア加算",
    "認知症ケア加算",
    "栄養サポートチーム加算",
    "褥瘡ハイリスク患者ケア加算"
]

MISSING_CANDIDATES = [
    ("看護補助体制加算", 0),
    ("急性期看護補助体制加算", 0),
    ("夜間看護補助加算", 0),
    ("医師事務作業補助体制加算", 0),
    ("診療録管理体制加算", 0),
    ("入退院支援加算", 0),
]


def _is_likely_facility_url(url: str) -> bool:
    u = url.lower()

    ng_keywords = [
        "indeed", "townwork", "rikunabi", "job-medley",
        "staffservice", "manpower", "hatarako", "baitoru",
        "en-gage", "career", "求人"
    ]
    for ng in ng_keywords:
        if ng in u:
            return False

    return True


def _collect_candidate_urls(hospital_name: str, area: str = "", hospital_info: dict | None = None):
    queries = []

    if area:
        queries += [
            f"{hospital_name} {area} 施設基準",
            f"{hospital_name} {area} 届出",
            f"{hospital_name} {area} 入院料",
            f"{hospital_name} {area} 看護補助体制加算",
            f"{hospital_name} {area} 医師事務作業補助体制加算",
        ]

    queries += [
        f"{hospital_name} 施設基準",
        f"{hospital_name} 届出",
        f"{hospital_name} 入院料",
        f"{hospital_name} 看護補助体制加算",
        f"{hospital_name} 医師事務作業補助体制加算",
    ]

    if hospital_info:
        region = hospital_info.get("地域", "")
        station = hospital_info.get("最寄駅", "")
        if region and region != "不明":
            queries += [
                f"{region} {hospital_name} 施設基準",
                f"{region} {hospital_name} 入院料",
            ]
        if station and station != "不明":
            queries += [
                f"{station} {hospital_name} 施設基準"
            ]

    results = []

    for query in queries:
        items = search_web(query)

        for item in items:
            url = item.get("url", "")
            if not url:
                continue
            if not _is_likely_facility_url(url):
                continue

            results.append({
                "title": item.get("title", ""),
                "url": url,
                "snippet": item.get("snippet", "")
            })

    deduped = []
    seen = set()

    for item in results:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        deduped.append(item)

    return deduped[:10]


def _extract_acquired_from_text(text: str):
    acquired = []

    for keyword in STANDARD_KEYWORDS:
        if keyword in text and keyword not in acquired:
            acquired.append(keyword)

    return acquired


def _merge_acquired(results):
    merged = []

    for r in results:
        for item in r.get("acquired", []):
            if item not in merged:
                merged.append(item)

    return merged


def _build_missing(acquired):
    missing = []

    for name, point in MISSING_CANDIDATES:
        if name not in acquired:
            missing.append((name, point))

    return missing


def get_facility_standard_debug(hospital_name: str, area: str = "", hospital_info: dict | None = None):
    candidate_urls = _collect_candidate_urls(hospital_name, area, hospital_info)

    page_details = []
    raw_results = []

    for item in candidate_urls[:6]:
        url = item["url"]
        title = item.get("title", "")

        text = fetch_page_text(url)
        fetched = bool(text)

        acquired = _extract_acquired_from_text(text) if text else []

        page_details.append({
            "title": title,
            "url": url,
            "fetched": fetched,
            "text_len": len(text) if text else 0,
            "acquired": acquired[:20]
        })

        raw_results.append({
            "url": url,
            "acquired": acquired
        })

    merged_acquired = _merge_acquired(raw_results)

    if not merged_acquired:
        # fallback: ここは暫定。今後精度改善予定
        merged_acquired = [
            "急性期一般入院料4",
            "看護補助体制加算",
            "医師事務作業補助体制加算"
        ]

    missing = _build_missing(merged_acquired)

    debug = {
        "candidate_url_count": len(candidate_urls),
        "page_details": page_details
    }

    return merged_acquired, missing, debug


def get_facility_standard(hospital_name: str, area: str = "", hospital_info: dict | None = None):
    acquired, missing, _ = get_facility_standard_debug(hospital_name, area, hospital_info)
    return acquired, missing
