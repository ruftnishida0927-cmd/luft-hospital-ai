# -*- coding: utf-8 -*-
import requests

def search_dispatch_jobs(hospital):

    # 仮ロジック（後でIndeed等スクレイピング）
    candidates = [
        {
            "派遣会社": "スタッフサービス・メディカル",
            "勤務地": "京都市東部",
            "職種": "看護助手",
            "一致度": "高"
        },
        {
            "派遣会社": "マンパワー",
            "勤務地": "宇治エリア",
            "職種": "医療事務",
            "一致度": "中"
        }
    ]

    return candidates
