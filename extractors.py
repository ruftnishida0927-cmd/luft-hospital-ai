# extractors.py
# -*- coding: utf-8 -*-

import re


PREFECTURES = [
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
    "内科", "外科", "整形外科", "精神科", "心療内科", "小児科", "皮膚科",
    "泌尿器科", "産婦人科", "婦人科", "脳神経外科", "脳神経内科", "眼科",
    "耳鼻咽喉科", "形成外科", "放射線科", "麻酔科", "リハビリテーション科",
    "呼吸器内科", "消化器内科", "循環器内科", "糖尿病内科", "腎臓内科",
    "救急科", "病理診断科",
]


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_prefecture(text: str) -> str:
    for p in PREFECTURES:
        if p in text:
            return p
    return "不明"


def extract_address(text: str) -> str:
    text = clean_text(text)

    # 住所系の候補
    patterns = [
        r"(所在地|住所)[:：]?\s*(" + "|".join(PREFECTURES) + r".{5,80}?)($|電話|TEL|アクセス|診療科|病床|FAX)",
        r"((" + "|".join(PREFECTURES) + r")[^ 　\n]{5,80})",
    ]

    candidates = []

    for pat in patterns:
        for m in re.finditer(pat, text):
            g = m.groups()
            cand = ""
            if len(g) >= 2:
                cand = g[1]
            elif len(g) >= 1:
                cand = g[0]

            cand = clean_text(cand)
            cand = re.sub(r"(電話|TEL|アクセス|診療科|病床|FAX).*$", "", cand).strip(" ：:")
            if any(pref in cand for pref in PREFECTURES):
                candidates.append(cand)

    if candidates:
        candidates = sorted(candidates, key=len, reverse=True)
        return candidates[0]

    return "不明"


def extract_region(address: str) -> str:
    if not address or address == "不明":
        return "不明"

    m = re.search(r"(北海道|..県|..府|東京都)(.{1,12}?(市|区|町|村))", address)
    if m:
        return clean_text(m.group(1) + m.group(2))

    p = extract_prefecture(address)
    if p != "不明":
        return p

    return "不明"


def extract_nearest_station(text: str) -> str:
    text = clean_text(text)

    patterns = [
        r"([^\s　]{1,20}駅)\s*(より)?\s*(徒歩|バス|車)\s*\d{1,2}分",
        r"(最寄り駅)[:：]?\s*([^\s　]{1,20}駅)",
        r"(アクセス)[:：]?\s*([^\s　]{1,20}駅)",
    ]

    for pat in patterns:
        m = re.search(pat, text)
        if m:
            groups = [g for g in m.groups() if g]
            for g in groups:
                if "駅" in g:
                    return clean_text(g)

    return "不明"


def extract_bed_count(text: str) -> str:
    text = clean_text(text)

    patterns = [
        r"病床数[:：]?\s*(\d{1,4})\s*床",
        r"(\d{1,4})\s*床",
    ]

    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return f"{m.group(1)}床"

    return "不明"


def extract_departments(text: str) -> str:
    found = []

    for dep in DEPARTMENT_KEYWORDS:
        if dep in text and dep not in found:
            found.append(dep)

    if found:
        return "、".join(found[:12])

    return "不明"


def extract_hospital_type(text: str, title: str = "") -> str:
    src = f"{title} {text}"

    explicit_types = [
        "精神科病院",
        "療養型病院",
        "ケアミックス病院",
        "一般病院",
        "大学病院",
        "総合病院",
        "リハビリテーション病院",
    ]

    for t in explicit_types:
        if t in src:
            return t

    return "不明"


def extract_hospital_name_from_title(title: str) -> str:
    if not title:
        return "不明"

    title = clean_text(title)
    title = re.sub(r"\s*[\-|｜|].*$", "", title).strip()

    if "病院" in title:
        return title

    return "不明"


def extract_basic_facts(text: str, title: str = "", url: str = "") -> dict:
    address = extract_address(text)
    region = extract_region(address)
    station = extract_nearest_station(text)
    bed_count = extract_bed_count(text)
    departments = extract_departments(text)
    hospital_type = extract_hospital_type(text, title=title)
    name_from_title = extract_hospital_name_from_title(title)

    return {
        "name_candidate": name_from_title,
        "address": address,
        "region": region,
        "nearest_station": station,
        "bed_count": bed_count,
        "departments": departments,
        "hospital_type": hospital_type,
    }
