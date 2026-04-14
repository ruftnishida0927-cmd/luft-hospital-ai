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

    # 郵便番号除去
    address = re.sub(r"〒?\d{3}-?\d{4}", "", address)

    # よくある記号ゆれ補正
    address = address.replace("−", "-").replace("ー", "-").replace("―", "-")
    address = address.replace("丁目", "-").replace("番地", "-").replace("番", "-").replace("号", "")

    # 末尾のアクセス情報っぽいもの除去を軽く
    address = re.sub(r"(徒歩.*|アクセス.*|最寄り駅.*)$", "", address)

    return address.strip("- ")


def normalize_station(station):
    station = normalize_text(station)
    station = station.replace("駅", "")
    return station


def normalize_region(region):
    return normalize_text(region)


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


def score_candidate(info, area=""):
    score = 0

    address = info.get("住所", "")
    region = info.get("地域", "不明")
    station = info.get("最寄駅", "不明")
    beds = info.get("病床数", "不明")
    deps = info.get("診療科", [])
    source = info.get("取得元", "")

    if address:
        score += 50
    if region not in ["", "不明", None]:
        score += 20
    if station not in ["", "不明", None]:
        score += 10
    if beds not in ["", "不明", None]:
        score += 10
    if deps and deps != ["調査中"]:
        score += 10

    if source == "official":
        score += 15
    elif source == "portal":
        score += 10
    elif source == "wiki":
        score += 5

    if area:
        if area in address or area == region or area in station:
            score += 25
        else:
            score -= 15

    if address and region == "不明":
        score -= 20

    if len(normalize_address(address)) < 8:
        score -= 10

    if station == "不明" and beds == "不明" and deps == ["調査中"]:
        score -= 20

    if score < 0:
        score = 0

    return score


def is_valid_candidate(info):
    address = info.get("住所", "")
    region = info.get("地域", "不明")
    station = info.get("最寄駅", "不明")
    beds = info.get("病床数", "不明")
    deps = info.get("診療科", ["調査中"])

    if not address and region == "不明":
        return False

    if (
        not address
        and station == "不明"
        and beds == "不明"
        and deps == ["調査中"]
    ):
        return False

    return True


def build_group_key(candidate):
    """
    同一病院判定用キー
    優先順位:
    1. 住所
    2. 地域 + 駅
    3. 地域 + 病床数
    """
    address = normalize_address(candidate.get("住所", ""))
    region = normalize_region(candidate.get("地域", ""))
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
    """
    同一病院と判断した候補を統合
    より情報量の多い方を優先しつつ、取得元はまとめる
    """
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

        # 両方入っているなら、長い方を優先
        return new if len(str(new)) > len(str(old)) else old

    merged["住所"] = prefer_value(base.get("住所"), new_one.get("住所"), ["", None])
    merged["地域"] = prefer_value(base.get("地域"), new_one.get("地域"))
    merged["最寄駅"] = prefer_value(base.get("最寄駅"), new_one.get("最寄駅"))
    merged["病床数"] = prefer_value(base.get("病床数"), new_one.get("病床数"))

    # 診療科は和集合
    old_deps = base.get("診療科", [])
    new_deps = new_one.get("診療科", [])
    merged_deps = []

    for dep in old_deps + new_deps:
        if dep not in merged_deps and dep != "調査中":
            merged_deps.append(dep)

    merged["診療科"] = merged_deps if merged_deps else ["調査中"]

    # フラグはOR
    merged["急性期"] = bool(base.get("急性期")) or bool(new_one.get("急性期"))
    merged["回復期"] = bool(base.get("回復期")) or bool(new_one.get("回復期"))
    merged["療養"] = bool(base.get("療養")) or bool(new_one.get("療養"))

    # URLは公式を優先
    base_source = base.get("取得元", "")
    new_source = new_one.get("取得元", "")

    if base_source != "official" and new_source == "official":
        merged["URL"] = new_one.get("URL", merged.get("URL", ""))

    # 取得元一覧を統合
    source_list = []
    for s in base.get("取得元一覧", [base_source]) + new_one.get("取得元一覧", [new_source]):
        if s and s not in source_list:
            source_list.append(s)

    merged["取得元一覧"] = source_list
    merged["取得元"] = " / ".join(source_list)

    # スコア再計算
    merged["スコア"] = score_candidate(merged, area)

    return merged


def merge_same_hospitals(candidates, area=""):
    grouped = {}

    for candidate in candidates:
        key = build_group_key(candidate)

        # 初回登録
        if key not in grouped:
            c = dict(candidate)
            source = c.get("取得元", "")
            c["取得元一覧"] = [source] if source else []
            c["スコア"] = score_candidate(c, area)
            grouped[key] = c
            continue

        # 既存候補と統合
        grouped[key] = merge_two_candidates(grouped[key], candidate, area)

    merged = list(grouped.values())
    merged.sort(key=lambda x: x.get("スコア", 0), reverse=True)
    return merged


def get_hospital_basic_info(name, area=""):
    candidate_sources = search_hospital_candidate_urls(name, area)

    raw_candidates = []

    for item in candidate_sources[:10]:
        url = item["url"]
        source = item.get("source", "other")

        text = fetch_page_text(url)

        if not text:
            continue

        info = build_info(text, name, url, source)

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
