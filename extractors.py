# -*- coding: utf-8 -*-
import re


PREFECTURES = [
    "北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県",
    "茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県",
    "新潟県","富山県","石川県","福井県","山梨県","長野県",
    "岐阜県","静岡県","愛知県","三重県",
    "滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県",
    "鳥取県","島根県","岡山県","広島県","山口県",
    "徳島県","香川県","愛媛県","高知県",
    "福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"
]

DEPARTMENTS = [
    "内科","外科","整形外科","小児科","皮膚科","泌尿器科","眼科",
    "耳鼻咽喉科","精神科","心療内科","リハビリテーション科",
    "脳神経外科","循環器内科","消化器内科","呼吸器内科",
    "救急科","形成外科","婦人科","産婦人科","麻酔科"
]

JOB_KEYWORDS = [
    "看護助手", "看護補助", "医療事務", "病棟クラーク", "医師事務",
    "外来クラーク", "受付", "一般事務", "入浴介助", "シーツ交換"
]


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\u3000", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_prefecture(text: str) -> str:
    text = normalize_text(text)
    for pref in PREFECTURES:
        if pref in text:
            return pref
    return "不明"


def extract_departments(text: str) -> list[str]:
    text = normalize_text(text)
    found = []
    for dep in DEPARTMENTS:
        if dep in text and dep not in found:
            found.append(dep)
    return found


def extract_bed_count(text: str):
    text = normalize_text(text)
    patterns = [
        r"(\d{1,4})\s*床",
        r"病床数[:：]?\s*(\d{1,4})",
        r"全?(\d{1,4})\s*床"
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    return None


def extract_walk_minutes(text: str):
    text = normalize_text(text)
    patterns = [
        r"徒歩\s*(\d{1,2})\s*分",
        r"駅から徒歩\s*(\d{1,2})\s*分",
        r"徒歩約\s*(\d{1,2})\s*分"
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    return None


def extract_station(text: str) -> str:
    text = normalize_text(text)
    patterns = [
        r"([^\s、。()（）]{1,12}駅)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return m.group(1)
    return "不明"


def extract_job_keywords(text: str) -> list[str]:
    text = normalize_text(text)
    found = []
    for keyword in JOB_KEYWORDS:
        if keyword in text and keyword not in found:
            found.append(keyword)
    return found


def extract_hospital_type_flags(text: str) -> dict:
    text = normalize_text(text)
    return {
        "急性期": "急性期" in text,
        "回復期": "回復期" in text,
        "療養": "療養" in text
    }


def build_job_features(text: str) -> dict:
    text = normalize_text(text)
    flags = extract_hospital_type_flags(text)

    return {
        "原文": text[:500],
        "地域": extract_prefecture(text),
        "最寄駅": extract_station(text),
        "徒歩分数": extract_walk_minutes(text),
        "病床数": extract_bed_count(text),
        "診療科": extract_departments(text),
        "職種キーワード": extract_job_keywords(text),
        "急性期": flags["急性期"],
        "回復期": flags["回復期"],
        "療養": flags["療養"],
    }
