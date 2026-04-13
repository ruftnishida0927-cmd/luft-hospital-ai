# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup

def get_hospital_basic_info(name):

    # 今は仮データ（後で実スクレイピングに変更）
    dummy = {
        "病院名": name,
        "病床数": 150,
        "病院種別": "一般病院",
        "地域": "京都府",
        "急性期": True,
        "回復期": False,
        "療養": False,
        "診療科": [
            "内科",
            "整形外科",
            "外科",
            "リハビリテーション科"
        ]
    }

    return dummy
