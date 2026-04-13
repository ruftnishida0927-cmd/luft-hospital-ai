# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup


def get_hospital_basic_info(name):

    try:
        url = f"https://www.google.com/search?q={name}+病床数"

        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5
        )

        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text()

        beds = "不明"

        for line in text.split("\n"):
            if "床" in line and "病床" in line:
                beds = line.strip()
                break

    except:
        beds = "取得失敗"

    info = {
        "病院名": name,
        "病床数": beds,
        "病院種別": "調査中",
        "地域": "調査中",
        "急性期": "調査中",
        "回復期": "調査中",
        "療養": "調査中",
        "診療科": ["調査中"]
    }

    return info
