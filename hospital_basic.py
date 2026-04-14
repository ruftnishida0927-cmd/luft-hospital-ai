# -*- coding: utf-8 -*-
import re

from extractors import (
    extract_prefecture,
    extract_address,
    extract_departments,
    extract_bed_count,
    extract_station,
    extract_hospital_type_flags
)
from source_hospital import search_hospital_candidate_urls
from search_provider import fetch_page_text


def normalize_text(value):
    if value is None:
        return ""
    value = str(value)
    value = value.replace("\u3000", " ")
    value = re.sub(r"\s+", "", value)
    return value.strip()


def normalize_address(address):
    address = normalize_text(address)
    address = re.sub(r"〒?\d{3}-?\d{4}", "", address)
    address = address.replace("−", "-").replace("ー", "-").replace("―", "-")
    address = address.replace("丁目", "-").replace("番地", "-").replace("番", "-").replace("号", "")
    return address.strip("- ")


def normalize_station(station):
    station = normalize_text(station)
    station = station.replace("駅", "")
    return station


def safe_int(v):
    try:
        return int(v)
    except:
        return None


def build_info(text, name, url, source):
    flags = extract_hospital_type_flags(text)

    return {
        "病院名": name,
        "病院種別": "一般病院",
        "住所": extract_address(text),
        "地域": extract_prefecture(text),
        "最寄駅": extract_station(text),
        "病床数": extract_bed_count(text) or "不明",
        "急性期": flags["急性期"],
        "回復期": flags["回復期"],
        "療養": flags["療養"],
        "診療科": extract_departments(text) or ["調査中"],
        "URL": url,
        "取得元": source
    }


def enrich_with_title_snippet(info, title="", snippet=""):
    """
    本文から取り切れない時の補助。
    title/snippet から地域や駅のヒントを補う
    """
    merged_text = f"{title}\n{snippet}"

    if info["地域"] in ["", "不明", None]:
        hint_region = extract_prefecture(merged_text)
        if hint_region not in ["", "不明", None]:
            info["地域"] = hint_region

    if info["最寄駅"] in ["", "不明", None]:
        hint_station = extract_station(merged_text)
        if hint_station not in ["", "不明", None]:
            info["最寄駅"] = hint_station

    return info


def score_candidate(info, area=""):
    score = 0

    address = info.get("住所", "")
    region = info.get("地域", "不明")
    station = info.get("最寄駅", "不明")
    beds = info.get("病床数", "不明")
    deps = info.get("診療科", [])
    source = info.get("取得元", "")

    # 基本点
    if address:
        score += 40

    if region not in ["", "不明", None]:
        score += 20

    if station not in ["", "不明", None]:
        score += 10

    if beds not in ["", "不明", None]:
        score += 10

    if deps and deps != ["調査中"]:
        score += 10

    # ソース加点
    if source == "official":
        score += 15
    elif source == "portal":
        score += 10
    elif source == "wiki":
        score += 5

    # エリア一致加点
    if area:
        if area in address or area == region or area in station:
            score += 30
        else:
            score -= 10

    # 住所がなくても地域+駅があれば残す
    if not address and region != "不明" and station != "不明":
        score += 10

    if score < 0:
        score = 0

    return score


def is_valid_candidate(info):
    """
    強く落としすぎない。
    住所がなくても、地域 or 駅 or 病床数があれば候補に残す
    """
    address = info.get("住所", "")
    region = info.get("地域", "不明")
    station = info.get("最寄駅", "不明")
    beds = info.get("病床数", "不明")
    deps = info.get("診療科", ["調査中"])

    if address:
        return True

    if region not in ["", "不明", None]:
        return True

    if station not in ["", "不明", None]:
        return True

    if beds not in ["", "不明", None]:
        return True

    if deps and deps != ["調査中"]:
        return True

    return False


def build_group_key(candidate):
    address = normalize_address(candidate.get("住所", ""))
    region = normalize_text(candidate.get("地域", ""))
    station = normalize_station(candidate.get("最寄駅", ""))
    beds = safe_int(candidate.get("病床数"))

    if address:
        return ("address", address)

    if region and region != "不明" and station and station != "不明":
        return ("region_station", region, station)

    if region and region != "不明" and beds is not None:
        return ("region_beds", region, beds)

    return (
        "fallback",
        normalize_text(candidate.get("病院名", "")),
        region,
        station,
        str(candidate.get("病床数", ""))
    )


def merge_two_candidates(base, new_one, area=""):
    merged = dict(base)

    def prefer_value(old, new, empty_values=None):
        if empty_values is None:
            empty_values = ["", "不明", None]

        old_empty = old in empty_values
        new_empty = new in empty_values

        if old_empty and not new_empty:
            return new
        if new_empty:
            return old

        return new if len(str(new)) > len(str(old)) else old

    merged["住所"] = prefer_value(base.get("住所"), new_one.get("住所"), ["", None])
    merged["地域"] = prefer_value(base.get("地域"), new_one.get("地域"))
    merged["最寄駅"] = prefer_value(base.get("最寄駅"), new_one.get("最寄駅"))
    merged["病床数"] = prefer_value(base.get("病床数"), new_one.get("病床数"))

    old_deps = base.get("診療科", [])
    new_deps = new_one.get("診療科", [])
    merged_deps = []

    for dep in old_deps + new_deps:
        if dep not in merged_deps and dep != "調査中":
            merged_deps.append(dep)

    merged["診療科"] = merged_deps if merged_deps else ["調査中"]

    merged["急性期"] = bool(base.get("急性期")) or bool(new_one.get("急性期"))
    merged["回復期"] = bool(base.get("回復期")) or bool(new_one.get("回復期"))
    merged["療養"] = bool(base.get("療養")) or bool(new_one.get("療養"))

    base_source = base.get("取得元", "")
    new_source = new_one.get("取得元", "")

    if base_source != "official" and new_source == "official":
        merged["URL"] = new_one.get("URL", merged.get("URL", ""))

    source_list = []
    for s in base.get("取得元一覧", [base_source]) + new_one.get("取得元一覧", [new_source]):
        if s and s not in source_list:
            source_list.append(s)

    merged["取得元一覧"] = source_list
    merged["取得元"] = " / ".join(source_list)
    merged["スコア"] = score_candidate(merged, area)

    return merged


def merge_same_hospitals(candidates, area=""):
    grouped = {}

    for candidate in candidates:
        key = build_group_key(candidate)

        if key not in grouped:
            c = dict(candidate)
            source = c.get("取得元", "")
            c["取得元一覧"] = [source] if source else []
            c["スコア"] = score_candidate(c, area)
            grouped[key] = c
            continue

        grouped[key] = merge_two_candidates(grouped[key], candidate, area)

    merged = list(grouped.values())
    merged.sort(key=lambda x: x.get("スコア", 0), reverse=True)
    return merged


def get_hospital_basic_info(name, area=""):
    candidate_sources = search_hospital_candidate_urls(name, area)

    raw_candidates = []

    for item in candidate_sources[:12]:
        url = item.get("url", "")
        source = item.get("source", "other")
        title = item.get("title", "")
        snippet = item.get("snippet", "")

        if not url:
            continue

        text = fetch_page_text(url)

        if not text:
            # 本文が取れなくても、title/snippetだけで最低限候補化
            text = f"{title}\n{snippet}"

        info = build_info(text, name, url, source)
        info = enrich_with_title_snippet(info, title, snippet)

        if is_valid_candidate(info):
            raw_candidates.append(info)

    if not raw_candidates:
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
            "URL": "",
            "取得元": "",
            "取得元一覧": [],
            "スコア": 0
        }]

    merged_candidates = merge_same_hospitals(raw_candidates, area)

    return merged_candidates
