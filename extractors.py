# -*- coding: utf-8 -*-
import re


PREFS = [
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


def normalize_text(text):
    if not text:
        return ""
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text


def extract_address_block(text):
    text = normalize_text(text)
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for i, line in enumerate(lines):
        if "〒" in line:
            return "\n".join(lines[i:i+6])

    for i, line in enumerate(lines):
        if any(pref in line for pref in PREFS):
            if any(x in line for x in ["市", "区", "町", "村"]):
                return "\n".join(lines[i:i+6])

    return "\n".join(lines[:10])


def extract_prefecture(text):
    block = extract_address_block(text)

    for pref in PREFS:
        if pref in block:
            return pref

    return "不明"


def extract_address(text):
    block = extract_address_block(text)
    lines = [line.strip() for line in block.split("\n") if line.strip()]

    for line in lines:
        if "〒" in line:
            return line

    for line in lines:
        if any(pref in line for pref in PREFS):
            if any(x in line for x in ["市", "区", "町", "村"]):
                return line

    return ""


def extract_station(text):
    block = extract_address_block(text)

    patterns = [
        r"最寄り駅[:：]?\s*([^\s、。()（）]{1,12}駅)",
        r"アクセス[:：]?\s*([^\s、。()（）]{1,12}駅)",
        r"([^\s、。()（）]{1,12}駅)"
    ]

    for pattern in patterns:
        m = re.search(pattern, block)
        if m:
            return m.group(1)

    return "不明"


def extract_bed_count(text):
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


def extract_departments(text):
    text = normalize_text(text)
    found = []

    for dep in DEPARTMENTS:
        if dep in text and dep not in found:
            found.append(dep)

    return found


def extract_hospital_type_flags(text):
    text = normalize_text(text)

    return {
        "急性期": "急性期" in text,
        "回復期": "回復期" in text,
        "療養": "療養" in text
    }
