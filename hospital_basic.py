# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup

from extractors import (
    extract_prefecture,
    extract_departments,
    extract_bed_count,
    extract_station,
    extract_hospital_type_flags
)


def search_mhlw(name):

    url = "https://www.iryou.teikyouseido.mhlw.go.jp/znk-web/juminkanja/S2300/initialize"

    try:
        r = requests.get(url, timeout=10)
    except:
        return []

    # 厚労省はPOST検索
    search_url = "https://www.iryou.teikyouseido.mhlw.go.jp/znk-web/juminkanja/S2300/"

    data = {
        "kikancd": "",
        "kikannm": name
    }

    try:
        r = requests.post(search_url, data=data, timeout=10)
    except:
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    results = []

    for tr in soup.select("tr"):

        text = tr.get_text()

        if name not in text:
            continue

        results.append(text)

    return results


def get_hospital_basic_info(name):

    results = search_mhlw(name)

    candidates = []

    for text in results:

        pref = extract_prefecture(text)

        info = {
            "病院名": name,
            "病院種別": "一般病院",
            "住所": text,
            "地域": pref,
            "最寄駅": extract_station(text),
            "病床数": extract_bed_count(text) or "不明",
            "急性期": False,
            "回復期": False,
            "療養": False,
            "診療科": ["調査中"],
            "URL": "厚労省"
        }

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

    return candidates
