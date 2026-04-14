# -*- coding: utf-8 -*-
from search_provider import search_web, fetch_page_text
from extractors import (
    extract_prefecture,
    extract_departments,
    extract_bed_count,
    extract_station,
    extract_hospital_type_flags
)


def extract_address(text):

    lines = text.split("\n")

    for line in lines:

        if "〒" in line:
            return line.strip()

        if "都" in line or "道" in line or "府" in line or "県" in line:
            if "市" in line or "区" in line or "町" in line:
                return line.strip()

    return ""


def build_info(text, name, url):

    address = extract_address(text)
    pref = extract_prefecture(text)
    flags = extract_hospital_type_flags(text)

    return {
        "病院名": name,
        "病院種別": "一般病院",
        "住所": address,
        "地域": pref,
        "最寄駅": extract_station(text),
        "病床数": extract_bed_count(text) or "不明",
        "急性期": flags["急性期"],
        "回復期": flags["回復期"],
        "療養": flags["療養"],
        "診療科": extract_departments(text) or ["調査中"],
        "URL": url
    }


def score_candidate(info):

    score = 0

    if info["住所"]:
        score += 50

    if info["地域"] != "不明":
        score += 20

    if info["最寄駅"] != "不明":
        score += 10

    if info["病床数"] != "不明":
        score += 10

    if info["診療科"] != ["調査中"]:
        score += 10

    return score


def get_hospital_basic_info(name):

    queries = [
        f"{name} 病院",
        f"{name} 病院 住所",
        f"{name} 医療法人",
        f"{name} 病院 アクセス"
    ]

    candidate_urls = []

    for query in queries:

        results = search_web(query)

        for r in results:
            candidate_urls.append(r["url"])

    # 重複除去
    seen = set()
    urls = []

    for u in candidate_urls:
        if u in seen:
            continue
        seen.add(u)
        urls.append(u)

    candidates = []

    for url in urls[:6]:

        text = fetch_page_text(url)

        if not text:
            continue

        info = build_info(text, name, url)
        candidates.append(info)

    if not candidates:
        return [{
            "病院名": name,
            "病院種別": "不明",
            "住所": "",
            "地域": "不明",
            "最寄駅": "不明",
            "病床数": "不明",
            "急性期": False,
            "回復期": False,
            "療養": False,
            "診療科": ["調査中"],
            "URL": ""
        }]

    candidates.sort(
        key=lambda x: score_candidate(x),
        reverse=True
    )

    return candidates
