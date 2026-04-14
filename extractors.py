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


def extract_prefecture(text):

    for p in PREFS:
        if p in text:
            return p

    return "不明"


def extract_station(text):

    m = re.search(
        r"([^\s、。]{1,12}駅)",
        text
    )

    if m:
        return m.group(1)

    return "不明"


def extract_bed_count(text):

    m = re.search(r"(\d{1,4})\s*床", text)

    if m:
        return int(m.group(1))

    return None


def extract_departments(text):

    deps = [
    "内科","外科","整形外科","小児科",
    "皮膚科","泌尿器科","精神科",
    "心療内科","眼科","耳鼻咽喉科"
    ]

    found = []

    for d in deps:
        if d in text:
            found.append(d)

    return found


def extract_hospital_type_flags(text):

    return {
        "急性期": "急性期" in text,
        "回復期": "回復期" in text,
        "療養": "療養" in text
    }
