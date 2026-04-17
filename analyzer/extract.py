# analyzer/extract.py
# -*- coding: utf-8 -*-

import re
from typing import Any, Dict, List


JP_PREFECTURES = [
    "北海道",
    "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県",
    "岐阜県", "静岡県", "愛知県", "三重県",
    "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県",
    "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県",
    "沖縄県",
]

DEPARTMENT_KEYWORDS = [
    "内科", "外科", "整形外科", "皮膚科", "泌尿器科", "眼科", "耳鼻咽喉科",
    "小児科", "産婦人科", "婦人科", "脳神経外科", "脳神経内科", "心療内科",
    "精神科", "形成外科", "リハビリテーション科", "放射線科", "麻酔科",
    "消化器内科", "消化器外科", "循環器内科", "呼吸器内科", "呼吸器外科",
    "腎臓内科", "糖尿病内科", "血液内科", "救急科", "総合診療科",
]

HOSPITAL_TYPE_KEYWORDS = [
    "病院", "クリニック", "診療所", "医院", "メディカルセンター",
]

HOSPITAL_FUNCTION_KEYWORDS = [
    "急性期", "回復期", "慢性期", "療養", "救急", "在宅", "透析", "訪問診療",
    "地域包括", "回復期リハビリテーション", "緩和ケア", "二次救急", "三次救急",
]

FACILITY_BASIC_RATE_KEYWORDS = [
    "急性期一般入院料",
    "地域一般入院料",
    "療養病棟入院基本料",
    "回復期リハビリテーション病棟入院料",
    "地域包括ケア病棟入院料",
    "精神病棟入院基本料",
    "特定機能病院入院基本料",
    "専門病院入院基本料",
]

FACILITY_ADDITION_KEYWORDS = [
    "看護補助体制加算",
    "夜間看護体制加算",
    "夜間急性期看護補助体制加算",
    "看護職員夜間配置加算",
    "医師事務作業補助体制加算",
    "診療録管理体制加算",
    "療養環境加算",
    "感染対策向上加算",
    "医療安全対策加算",
    "入退院支援加算",
    "データ提出加算",
    "栄養サポートチーム加算",
    "褥瘡ハイリスク患者ケア加算",
    "せん妄ハイリスク患者ケア加算",
]

RECRUIT_DEPARTMENT_KEYWORDS = [
    "採用担当", "人事", "総務", "事務部", "管理部", "看護部", "事務長",
]

GROUP_KEYWORDS = [
    "医療法人", "社会医療法人", "学校法人", "グループ", "関連施設", "法人本部",
    "系列", "運営法人",
]

CONTACT_LINE_KEYWORDS = [
    "お問い合わせ", "問い合わせ", "連絡先", "代表", "採用", "応募", "メール", "電話",
]

REGEX_PATTERNS = {
    "address": [
        r"(?:住所|所在地)\s*[：:\-]?\s*([^\n]{6,120})",
        r"((?:北海道|東京都|京都府|大阪府|.{2,3}県).{4,80})",
    ],
    "phone": [
        r"(?:TEL|Tel|tel|電話番号|電話)\s*[：:\-]?\s*(0\d{1,4}-\d{1,4}-\d{3,4})",
        r"\b(0\d{1,4}-\d{1,4}-\d{3,4})\b",
    ],
    "email": [
        r"([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})",
    ],
    "bed_count": [
        r"(?:病床数|病床|許可病床数)\s*[：:\-]?\s*(\d{1,4})\s*床",
        r"(\d{1,4})\s*床",
    ],
    "nearest_station": [
        r"(?:最寄駅|アクセス)\s*[：:\-]?\s*([^\n]{2,80})",
        r"([^\n]{1,30}駅(?:から)?(?:徒歩|バス)[^\n]{0,30})",
    ],
    "corporation_name": [
        r"((?:社会医療法人|医療法人社団|医療法人財団|医療法人|学校法人)[^\n]{2,80})",
    ],
    "contact_person": [
        r"(?:採用担当|担当者)\s*[：:\-]?\s*([^\n]{1,30})",
    ],
}


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r", "\n")
    text = re.sub(r"\u3000", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _lines(text: str) -> List[str]:
    cleaned = _clean_text(text)
    rows = []
    for line in cleaned.split("\n"):
        line = line.strip()
        if not line:
            continue
        rows.append(line)
    return rows


def _dedupe_str_list(values: List[str]) -> List[str]:
    seen = set()
    result = []
    for v in values:
        x = (v or "").strip()
        if not x:
            continue
        if x in seen:
            continue
        seen.add(x)
        result.append(x)
    return result


def _mk_evidence(
    field: str,
    value: str,
    page: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "field": field,
        "value": (value or "").strip(),
        "url": page.get("url", ""),
        "source_type": page.get("source_type", "unknown"),
        "source_label": page.get("label", "") or page.get("title", "") or page.get("url", ""),
        "page_category": page.get("category", "unknown"),
    }


def _find_by_patterns(field: str, text: str, page: Dict[str, Any]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for pattern in REGEX_PATTERNS.get(field, []):
        try:
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
        except re.error:
            continue
        for match in matches:
            value = match if isinstance(match, str) else " ".join(match)
            value = value.strip(" 　:：-")
            if len(value) < 2:
                continue
            results.append(_mk_evidence(field, value, page))
    return results


def _find_prefecture(text: str, page: Dict[str, Any]) -> List[Dict[str, Any]]:
    results = []
    for pref in JP_PREFECTURES:
        if pref in text:
            results.append(_mk_evidence("region", pref, page))
    return results


def _find_departments(text: str, page: Dict[str, Any]) -> List[Dict[str, Any]]:
    results = []
    hits = [kw for kw in DEPARTMENT_KEYWORDS if kw in text]
    if hits:
        results.append(_mk_evidence("departments", "、".join(_dedupe_str_list(hits)), page))
    return results


def _find_hospital_type(text: str, page: Dict[str, Any]) -> List[Dict[str, Any]]:
    results = []
    hits = [kw for kw in HOSPITAL_TYPE_KEYWORDS if kw in text]
    if hits:
        results.append(_mk_evidence("hospital_type", "、".join(_dedupe_str_list(hits)), page))
    return results


def _find_hospital_function(text: str, page: Dict[str, Any]) -> List[Dict[str, Any]]:
    results = []
    hits = [kw for kw in HOSPITAL_FUNCTION_KEYWORDS if kw in text]
    if hits:
        results.append(_mk_evidence("hospital_function", "、".join(_dedupe_str_list(hits)), page))
    return results


def _find_facility_items(text: str, page: Dict[str, Any]) -> Dict[str, List[str]]:
    basic_rates = []
    additions = []

    for kw in FACILITY_BASIC_RATE_KEYWORDS:
        if kw in text:
            basic_rates.append(kw)

    for kw in FACILITY_ADDITION_KEYWORDS:
        if kw in text:
            additions.append(kw)

    return {
        "basic_rates": _dedupe_str_list(basic_rates),
        "additions": _dedupe_str_list(additions),
        "lines": _extract_keyword_lines(text, FACILITY_BASIC_RATE_KEYWORDS + FACILITY_ADDITION_KEYWORDS),
    }


def _extract_keyword_lines(text: str, keywords: List[str]) -> List[str]:
    rows = _lines(text)
    picked = []
    for row in rows:
        if any(kw in row for kw in keywords):
            picked.append(row)
    return _dedupe_str_list(picked)


def _find_recruit_items(text: str, page: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    evidences: Dict[str, List[Dict[str, Any]]] = {
        "contact_person": [],
        "department": [],
        "phone": [],
        "email": [],
    }

    evidences["contact_person"].extend(_find_by_patterns("contact_person", text, page))
    evidences["phone"].extend(_find_by_patterns("phone", text, page))
    evidences["email"].extend(_find_by_patterns("email", text, page))

    rows = _extract_keyword_lines(text, RECRUIT_DEPARTMENT_KEYWORDS + ["採用", "応募", "求人"])
    for row in rows:
        for kw in RECRUIT_DEPARTMENT_KEYWORDS:
            if kw in row:
                evidences["department"].append(_mk_evidence("department", kw, page))

    return evidences


def _find_group_items(text: str, page: Dict[str, Any]) -> Dict[str, List[str]]:
    hits = []
    for kw in GROUP_KEYWORDS:
        if kw in text:
            hits.append(kw)

    rows = _extract_keyword_lines(text, GROUP_KEYWORDS)
    return {
        "related_facilities": _dedupe_str_list(hits),
        "group_lines": rows,
    }


def _find_contact_lines(text: str) -> List[str]:
    return _extract_keyword_lines(text, CONTACT_LINE_KEYWORDS)


def extract_evidences(
    pages: List[Dict[str, Any]],
    hospital_name: str = "",
    prefecture: str = "",
) -> Dict[str, Any]:
    basic: Dict[str, List[Dict[str, Any]]] = {
        "address": [],
        "region": [],
        "nearest_station": [],
        "bed_count": [],
        "departments": [],
        "hospital_type": [],
        "hospital_function": [],
        "corporation_name": [],
        "phone": [],
        "email": [],
    }

    facility = {
        "basic_rates": [],
        "additions": [],
        "official_lines": [],
        "public_lines": [],
    }

    recruit: Dict[str, List[Dict[str, Any]] | List[str]] = {
        "contact_person": [],
        "department": [],
        "phone": [],
        "email": [],
        "contact_lines": [],
    }

    group = {
        "related_facilities": [],
        "group_lines": [],
    }

    contact: Dict[str, List[Dict[str, Any]] | List[str]] = {
        "phone": [],
        "email": [],
        "contact_lines": [],
    }

    for page in pages or []:
        text = _clean_text(page.get("text", "") or page.get("content", "") or "")
        if not text:
            continue

        page_category = page.get("category", "unknown")
        source_type = page.get("source_type", "unknown")

        basic["address"].extend(_find_by_patterns("address", text, page))
        basic["nearest_station"].extend(_find_by_patterns("nearest_station", text, page))
        basic["bed_count"].extend(_find_by_patterns("bed_count", text, page))
        basic["corporation_name"].extend(_find_by_patterns("corporation_name", text, page))
        basic["phone"].extend(_find_by_patterns("phone", text, page))
        basic["email"].extend(_find_by_patterns("email", text, page))
        basic["region"].extend(_find_prefecture(text, page))
        basic["departments"].extend(_find_departments(text, page))
        basic["hospital_type"].extend(_find_hospital_type(text, page))
        basic["hospital_function"].extend(_find_hospital_function(text, page))

        facility_items = _find_facility_items(text, page)
        facility["basic_rates"].extend(facility_items["basic_rates"])
        facility["additions"].extend(facility_items["additions"])

        if source_type == "public" or page_category == "public":
            facility["public_lines"].extend(facility_items["lines"])
        else:
            facility["official_lines"].extend(facility_items["lines"])

        recruit_items = _find_recruit_items(text, page)
        recruit["contact_person"].extend(recruit_items["contact_person"])
        recruit["department"].extend(recruit_items["department"])
        recruit["phone"].extend(recruit_items["phone"])
        recruit["email"].extend(recruit_items["email"])
        recruit["contact_lines"].extend(_extract_keyword_lines(text, ["採用", "応募", "求人", "人事", "総務", "問い合わせ"]))

        group_items = _find_group_items(text, page)
        group["related_facilities"].extend(group_items["related_facilities"])
        group["group_lines"].extend(group_items["group_lines"])

        contact["phone"].extend(_find_by_patterns("phone", text, page))
        contact["email"].extend(_find_by_patterns("email", text, page))
        contact["contact_lines"].extend(_find_contact_lines(text))

    if prefecture:
        basic["region"].insert(0, _mk_evidence("region", prefecture, {
            "url": "",
            "source_type": "input",
            "label": "入力都道府県",
            "category": "input",
            "title": "",
        }))

    facility["basic_rates"] = _dedupe_str_list(facility["basic_rates"])
    facility["additions"] = _dedupe_str_list(facility["additions"])
    facility["official_lines"] = _dedupe_str_list(facility["official_lines"])
    facility["public_lines"] = _dedupe_str_list(facility["public_lines"])
    recruit["contact_lines"] = _dedupe_str_list(recruit["contact_lines"])
    group["related_facilities"] = _dedupe_str_list(group["related_facilities"])
    group["group_lines"] = _dedupe_str_list(group["group_lines"])
    contact["contact_lines"] = _dedupe_str_list(contact["contact_lines"])

    return {
        "basic": basic,
        "facility": facility,
        "recruit": recruit,
        "group": group,
        "contact": contact,
    }
