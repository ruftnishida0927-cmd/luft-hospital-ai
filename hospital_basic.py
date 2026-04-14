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
        line = line.strip()

        if not line:
            continue

        if "〒" in line:
            return line

        if any(x in line for x in ["都", "道", "府", "県"]):
            if any(y in line for y in ["市", "区", "町", "村"]):
                return line

    return ""


def build_info(text, name, url):
    address = extract_address(text)
    pref = extract_prefecture(text)
    flags = extract_hospital_type_flags(text)
    beds = extract_bed_count(text)
    station = extract_station(text)
    deps = extract_departments(text)

    return {
        "病院名": name,
        "病院種別": "一般病院",
        "住所": address,
        "地域": pref if pref else "不明",
        "最寄駅": station if station else "不明",
        "病床数": beds if beds else "不明",
        "急性期": flags["急性期"],
        "回復期": flags["回復期"],
        "療養": flags["療養"],
        "診療科": deps if deps else ["調査中"],
        "URL": url
    }


def score_info(info):
    score = 0

    if info.get("住所"):
        score += 50

    if info.get("地域") not in ["", "不明", None]:
        score += 20

    if info.get("最寄駅") not in ["", "不明", None]:
        score += 10

    if info.get("病床数") not in ["", "不明", None]:
        score += 10

    deps = info.get("診療科", [])
    if deps and deps != ["調査中"]:
        score += 10

    return score


def is_valid_candidate(info, name):
    # 最低限、住所か地域のどちらかは欲しい
    has_address = bool(info.get("住所"))
    has_region = info.get("地域") not in ["", "不明", None]

    if not has_address and not has_region:
        return False

    # 病院名が本文から全く拾えなくても候補には残すが、
    # 情報が薄いページは弾く
    thin_info = (
        info.get("病床数") in ["", "不明", None]
        and info.get("最寄駅") in ["", "不明", None]
        and info.get("診療科") == ["調査中"]
    )

    if thin_info and not has_address:
        return False

    return True


def dedupe_candidates(candidates):
    deduped = []
    seen = set()

    for c in candidates:
        key = (
            c.get("住所", ""),
            c.get("地域", ""),
            c.get("最寄駅", ""),
            str(c.get("病床数", "")),
            c.get("URL", "")
        )

        if key in seen:
            continue

        seen.add(key)
        deduped.append(c)

    return deduped


def get_hospital_basic_info(name):
    queries = [
        f"{name} 病院 住所",
        f"{name} 病院 所在地",
        f"{name} 病院 アクセス",
        f"{name} 医療法人",
        f"{name} 病院 公式"
    ]

    candidate_urls = []

    for query in queries:
        results = search_web(query)

        for r in results:
            url = r.get("url", "")
            if not url:
                continue
            candidate_urls.append(url)

    # URL重複削除
    deduped_urls = []
    seen = set()

    for u in candidate_urls:
        if u in seen:
            continue
        seen.add(u)
        deduped_urls.append(u)

    candidates = []

    for url in deduped_urls[:8]:
        text = fetch_page_text(url)

        if not text:
            continue

        info = build_info(text, name, url)

        if is_valid_candidate(info, name):
            candidates.append(info)

    candidates = dedupe_candidates(candidates)

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

    candidates.sort(key=score_info, reverse=True)

    return candidates
