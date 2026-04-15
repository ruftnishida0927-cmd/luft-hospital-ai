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

# 系統ごとの候補
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
            f"{hospital_name} {area} 基本診療料",
            f"{hospital_name} {area} 入院料",
            f"{hospital_name} {area} 看護補助",
            f"{hospital_name} {area} 医師事務作業補助体制加算",
        ]

    queries += [
        f"{hospital_name} 施設基準",
        f"{hospital_name} 基本診療料",
        f"{hospital_name} 入院料",
        f"{hospital_name} 看護補助",
        f"{hospital_name} 医師事務作業補助体制加算",
        f"{hospital_name} 届出",
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


def _extract_base_standard(text: str):
    norm = _normalize_text(text)

    found = []
    for label, patterns in BASE_STANDARD_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, norm):
                found.append(label)
                break

    # 基本料は複数拾っても、実務上はまず1系統に寄せる
    # ここでは最初に見つかったものを主系列とする
    if found:
        return found[0], found

    return None, []


def _extract_additional_standards(text: str):
    norm = _normalize_text(text)

    found = []
    for label, patterns in ADDITIONAL_STANDARD_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, norm):
                if label not in found:
                    found.append(label)
                break

    return found


def _classify_base_family(base_standard: str | None):
    if not base_standard:
        return "不明"

    if "急性期一般入院料" in base_standard:
        return "急性期"

    if "地域一般入院料" in base_standard:
        return "地域一般"

    if "障害者施設等入院基本料" in base_standard:
        return "障害者"

    if "療養病棟入院基本料" in base_standard:
        return "療養"

    if "回復期リハビリテーション病棟入院料" in base_standard:
        return "回復期"

    if "地域包括ケア病棟入院料" in base_standard:
        return "包括ケア"

    return "不明"


def _remove_incompatible_additions(base_family: str, additions: list[str]):
    cleaned = []

    for item in additions:
        # 障害者病棟なのに急性期看護補助体制加算は矛盾
        if base_family == "障害者" and item == "急性期看護補助体制加算":
            continue

        # 急性期系で「看護補助加算1/2」は障害者・療養寄りなので落とす
        if base_family == "急性期" and item in ["看護補助加算", "看護補助加算1", "看護補助加算2"]:
            continue

        # 療養で急性期看護補助体制加算は矛盾
        if base_family == "療養" and item == "急性期看護補助体制加算":
            continue

        cleaned.append(item)

    deduped = []
    for c in cleaned:
        if c not in deduped:
            deduped.append(c)

    return deduped


def _merge_acquired(page_results):
    base_candidates = []
    additions = []

    for r in page_results:
        if r.get("base_standard"):
            base_candidates.append(r["base_standard"])

        for item in r.get("additional_standards", []):
            if item not in additions:
                additions.append(item)

    base_standard = base_candidates[0] if base_candidates else None
    base_family = _classify_base_family(base_standard)
    additions = _remove_incompatible_additions(base_family, additions)

    acquired = []
    if base_standard:
        acquired.append(base_standard)

    acquired.extend(additions)

    return acquired, base_standard, base_family


def _build_missing(acquired, base_family: str):
    candidates = MISSING_BY_BASE.get(base_family, [])

    missing = []
    for name, point in candidates:
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

        base_standard, base_hits = _extract_base_standard(text) if text else (None, [])
        additions = _extract_additional_standards(text) if text else []

        page_details.append({
            "title": title,
            "url": url,
            "fetched": fetched,
            "text_len": len(text) if text else 0,
            "base_standard": base_standard or "",
            "base_hits": base_hits[:10],
            "additional_standards": additions[:20]
        })

        raw_results.append({
            "url": url,
            "base_standard": base_standard,
            "additional_standards": additions
        })

    acquired, base_standard, base_family = _merge_acquired(raw_results)
    missing = _build_missing(acquired, base_family)

    debug = {
        "candidate_url_count": len(candidate_urls),
        "base_standard": base_standard or "不明",
        "base_family": base_family,
        "page_details": page_details
    }

    return acquired, missing, debug


def get_facility_standard(hospital_name: str, area: str = "", hospital_info: dict | None = None):
    acquired, missing, _ = get_facility_standard_debug(hospital_name, area, hospital_info)
    return acquired, missing
