# -*- coding: utf-8 -*-
from typing import Any


def _score_station(hospital_info: dict, job_features: dict):
    hospital_station = str(hospital_info.get("最寄駅", "不明"))
    job_station = str(job_features.get("最寄駅", "不明"))

    if hospital_station == "不明" or job_station == "不明":
        return 0, None

    if hospital_station == job_station:
        return 25, f"最寄駅一致: {hospital_station}"

    if hospital_station.replace("駅", "") in job_station or job_station.replace("駅", "") in hospital_station:
        return 18, f"最寄駅近似一致: {hospital_station} / {job_station}"

    return 0, None


def _score_region(hospital_info: dict, job_features: dict):
    hospital_region = str(hospital_info.get("地域", "不明"))
    job_region = str(job_features.get("地域", "不明"))

    if hospital_region == "不明" or job_region == "不明":
        return 0, None

    if hospital_region == job_region:
        return 15, f"地域一致: {hospital_region}"

    return 0, None


def _score_beds(hospital_info: dict, job_features: dict):
    hospital_beds = hospital_info.get("病床数")
    job_beds = job_features.get("病床数")

    if not isinstance(hospital_beds, int) or not isinstance(job_beds, int):
        return 0, None

    diff = abs(hospital_beds - job_beds)

    if diff <= 20:
        return 20, f"病床数が非常に近い: {hospital_beds}床 / {job_beds}床"
    if diff <= 50:
        return 12, f"病床数が近い: {hospital_beds}床 / {job_beds}床"
    if diff <= 100:
        return 6, f"病床数がやや近い: {hospital_beds}床 / {job_beds}床"

    return 0, None


def _score_walk(job_features: dict):
    walk = job_features.get("徒歩分数")

    if not isinstance(walk, int):
        return 0, None

    if walk <= 5:
        return 10, f"徒歩分数が短い: 徒歩{walk}分"
    if walk <= 10:
        return 7, f"徒歩分数が近い: 徒歩{walk}分"
    if walk <= 15:
        return 4, f"徒歩圏候補: 徒歩{walk}分"

    return 0, None


def _score_departments(hospital_info: dict, job_features: dict):
    hospital_deps = hospital_info.get("診療科", [])
    job_deps = job_features.get("診療科", [])

    if not hospital_deps or not job_deps:
        return 0, None

    common = [d for d in hospital_deps if d in job_deps]
    if not common:
        return 0, None

    score = min(15, len(common) * 5)
    return score, f"診療科一致: {', '.join(common)}"


def _score_type_flags(hospital_info: dict, job_features: dict):
    score = 0
    reasons = []

    for key in ["急性期", "回復期", "療養"]:
        if bool(hospital_info.get(key)) and bool(job_features.get(key)):
            score += 10
            reasons.append(f"{key}一致")

    if not reasons:
        return 0, None

    return min(score, 20), " / ".join(reasons)


def _score_job_keywords(job_features: dict):
    jobs = job_features.get("職種キーワード", [])
    if not jobs:
        return 0, None

    score = min(10, len(jobs) * 3)
    return score, f"職種キーワード抽出: {', '.join(jobs)}"


def build_match_result(hospital_info: dict, job_features: dict) -> dict[str, Any]:
    total = 0
    reasons = []

    scorers = [
        _score_station(hospital_info, job_features),
        _score_region(hospital_info, job_features),
        _score_beds(hospital_info, job_features),
        _score_walk(job_features),
        _score_departments(hospital_info, job_features),
        _score_type_flags(hospital_info, job_features),
        _score_job_keywords(job_features),
    ]

    for score, reason in scorers:
        total += score
        if reason:
            reasons.append(reason)

    if total > 100:
        total = 100

    if total >= 85:
        judgment = "かなり有力"
    elif total >= 70:
        judgment = "有力候補"
    elif total >= 55:
        judgment = "候補"
    else:
        judgment = "参考"

    return {
        "一致率": total,
        "判定": judgment,
        "根拠": reasons
    }
