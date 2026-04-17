from __future__ import annotations

import re
from typing import Dict, List

from .models import Evidence, Page
from .utils import extract_prefecture, is_japanese_address, normalize_space, unique_keep_order

BASIC_PATTERNS = {
    "住所": [r"(?:住所|所在地)[:：]?\s*([^
。]{8,120})"],
    "代表電話": [r"(?:TEL|電話番号|代表)[:：]?\s*(0\d{1,4}-\d{1,4}-\d{3,4})"],
    "メール": [r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"],
    "病床数": [r"(\d{1,4})\s*床"],
    "最寄駅": [r"最寄(?:り)?駅[:：]?\s*([^。\n]{2,40})", r"(?:JR|阪急|阪神|京阪|近鉄|地下鉄|東京メトロ|西鉄)[^。\n]{1,30}駅"],
    "法人名": [r"(医療法人[^\s　]{1,40})", r"(社会医療法人[^\s　]{1,40})", r"(一般財団法人[^\s　]{1,40})", r"(公益社団法人[^\s　]{1,40})"],
}

DEPARTMENT_KEYWORDS = [
    "内科", "外科", "整形外科", "精神科", "心療内科", "皮膚科", "泌尿器科", "産婦人科", "婦人科", "眼科", "耳鼻咽喉科",
    "小児科", "神経内科", "脳神経外科", "放射線科", "麻酔科", "リハビリテーション科", "透析", "救急科", "歯科", "消化器内科",
]

HOSPITAL_TYPE_HINTS = {
    "一般病院": ["病院", "一般病床", "急性期"],
    "療養型": ["療養病床", "慢性期", "療養"],
    "精神科病院": ["精神科病院", "精神病床", "こころ"],
    "有床診療所": ["診療所", "有床"],
    "無床診療所": ["診療所", "無床"],
}

FUNCTION_HINTS = {
    "急性期": ["急性期", "救急", "一般病床", "手術", "ER"],
    "回復期": ["回復期", "地域包括ケア", "リハビリ"],
    "慢性期": ["慢性期", "療養病床", "療養"],
    "在宅": ["訪問診療", "在宅", "往診"],
    "透析": ["透析", "血液浄化"],
    "救急": ["救急", "二次救急", "救急告示"],
}

BASIC_FEE_KEYWORDS = [
    "入院基本料", "特定入院料", "急性期一般入院料", "地域包括ケア病棟入院料", "療養病棟入院基本料",
    "回復期リハビリテーション病棟入院料", "精神病棟入院基本料", "結核病棟入院基本料",
]

ADDON_KEYWORDS = [
    "加算", "補助体制", "夜間", "感染対策", "医師事務作業補助体制", "看護補助体制", "医療安全対策", "栄養サポート",
]

CONTACT_TITLE_HINTS = ["採用", "求人", "問い合わせ", "お問い合わせ", "連絡先"]


def extract_evidences(pages: List[Page]) -> Dict[str, List[Evidence]]:
    out: Dict[str, List[Evidence]] = {}
    for page in pages:
        text = normalize_space(page.text)
        if not text:
            continue
        for field, patterns in BASIC_PATTERNS.items():
            for pat in patterns:
                for m in re.finditer(pat, text, re.I):
                    val = normalize_space(m.group(1) if m.groups() else m.group(0))
                    if field == "住所" and not is_japanese_address(val):
                        continue
                    if field == "病床数":
                        val = f"{val}床"
                    _append(out, field, Evidence(field, val, page.final_url, page.title or page.final_url, page.category, page.source_type, _score(page), f"regex:{field}"))
                    break

        departments = [kw for kw in DEPARTMENT_KEYWORDS if kw in text]
        if departments:
            val = "、".join(unique_keep_order(departments))
            _append(out, "診療科", Evidence("診療科", val, page.final_url, page.title or page.final_url, page.category, page.source_type, _score(page), "keyword:departments"))

        address_candidates = re.findall(r"(北海道|東京都|京都府|大阪府|.{2,3}県[^。\n]{4,60})", text)
        for cand in address_candidates[:3]:
            if is_japanese_address(cand):
                _append(out, "住所", Evidence("住所", normalize_space(cand), page.final_url, page.title or page.final_url, page.category, page.source_type, _score(page), "heuristic:address"))

        pref = extract_prefecture(text)
        if pref != "不明":
            _append(out, "地域", Evidence("地域", pref, page.final_url, page.title or page.final_url, page.category, page.source_type, _score(page), "heuristic:prefecture"))

        for type_name, hints in HOSPITAL_TYPE_HINTS.items():
            if any(h in text for h in hints):
                _append(out, "病院種別", Evidence("病院種別", type_name, page.final_url, page.title or page.final_url, page.category, page.source_type, _score(page), "heuristic:hospital_type"))

        funcs = [name for name, hints in FUNCTION_HINTS.items() if any(h in text for h in hints)]
        if funcs:
            _append(out, "病院機能", Evidence("病院機能", "、".join(unique_keep_order(funcs)), page.final_url, page.title or page.final_url, page.category, page.source_type, _score(page), "heuristic:function"))

        for line in _split_semantic_lines(text):
            if any(k in line for k in BASIC_FEE_KEYWORDS):
                _append(out, "施設基準_基本料", Evidence("施設基準_基本料", line, page.final_url, page.title or page.final_url, page.category, page.source_type, _score(page, facility_boost=True), "line:basic_fee"))
            elif any(k in line for k in ADDON_KEYWORDS):
                _append(out, "施設基準_加算", Evidence("施設基準_加算", line, page.final_url, page.title or page.final_url, page.category, page.source_type, _score(page, facility_boost=True), "line:addon"))

        if page.category in {"contact", "recruit"} or any(h in text for h in CONTACT_TITLE_HINTS):
            for tel in re.findall(r"0\d{1,4}-\d{1,4}-\d{3,4}", text):
                _append(out, "採用電話", Evidence("採用電話", tel, page.final_url, page.title or page.final_url, page.category, page.source_type, _score(page), "regex:tel"))
            for mail in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
                _append(out, "採用メール", Evidence("採用メール", mail, page.final_url, page.title or page.final_url, page.category, page.source_type, _score(page), "regex:mail"))
            dept_hit = re.search(r"((採用担当|人事部|総務部|事務部|事務局|看護部|人材開発部)[^。\n]{0,20})", text)
            if dept_hit:
                _append(out, "採用担当部署", Evidence("採用担当部署", normalize_space(dept_hit.group(1)), page.final_url, page.title or page.final_url, page.category, page.source_type, _score(page), "regex:recruit_dept"))

        for grp in re.findall(r"((?:医療法人|社会医療法人|一般財団法人|公益社団法人)[^。\n]{1,40})", text):
            _append(out, "関連法人候補", Evidence("関連法人候補", normalize_space(grp), page.final_url, page.title or page.final_url, page.category, page.source_type, _score(page), "regex:corp"))

        for line in _split_semantic_lines(text):
            if any(k in line for k in ["関連施設", "グループ", "施設一覧", "病院一覧", "勤務地一覧"]):
                _append(out, "関連施設候補", Evidence("関連施設候補", line, page.final_url, page.title or page.final_url, page.category, page.source_type, _score(page), "line:group"))
    return out


def _append(out: Dict[str, List[Evidence]], key: str, ev: Evidence):
    out.setdefault(key, []).append(ev)


def _score(page: Page, facility_boost: bool = False) -> float:
    base = 0.45
    if page.source_type == "public":
        base += 0.25
    elif page.source_type == "official":
        base += 0.2
    elif page.source_type == "recruit":
        base += 0.1
    if page.category in {"basic", "facility", "recruit", "group", "contact", "public"}:
        base += 0.1
    if facility_boost and page.category in {"facility", "public"}:
        base += 0.15
    return min(base, 0.98)


def _split_semantic_lines(text: str) -> List[str]:
    text = text.replace("。", "\n").replace("・", "\n")
    lines = [normalize_space(x) for x in re.split(r"[\n\r]+", text)]
    return [x[:220] for x in lines if len(x) >= 4]
