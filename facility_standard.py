# -*- coding: utf-8 -*-

def get_facility_standard(name):

    # 仮データ（後で厚生局スクレイピングに変更）
    acquired = [
        "急性期一般入院料4",
        "看護補助体制加算",
        "医師事務作業補助体制加算"
    ]

    missing = [
        ("急性期看護補助体制加算25:1", 420),
        ("夜間看護補助加算", 160),
        ("医師事務作業補助体制加算50:1", 300)
    ]

    return acquired, missing
