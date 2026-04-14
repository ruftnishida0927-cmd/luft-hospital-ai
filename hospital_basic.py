# -*- coding: utf-8 -*-

from source_hospital import (
    search_google,
    search_wikipedia,
    search_mhlw
)


def score_candidate(c):

    score = 0

    if c["地域"] != "不明":
        score += 40

    if c["最寄駅"] != "不明":
        score += 20

    if c["病床数"]:
        score += 10

    return score


def merge_candidates(name, candidates):

    best = None
    best_score = -1

    for c in candidates:

        score = score_candidate(c)

        if score > best_score:
            best = c
            best_score = score

    return {
        "病院名": name,
        "病院種別": "一般病院",
        "住所": best["住所"],
        "地域": best["地域"],
        "最寄駅": best["最寄駅"],
        "病床数": best["病床数"] or "不明",
        "急性期": False,
        "回復期": False,
        "療養": False,
        "診療科": ["調査中"],
        "URL": best["source"]
    }


def get_hospital_basic_info(name):

    candidates = []

    candidates += search_google(name)
    candidates += search_wikipedia(name)
    candidates += search_mhlw(name)

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

    best = merge_candidates(name, candidates)

    return [best]
