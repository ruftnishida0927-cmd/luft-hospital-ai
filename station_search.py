# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup

def get_station(hospital):

    try:
        url = f"https://www.google.com/search?q={hospital}+最寄り駅"

        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5
        )

        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text()

        # 簡易駅抽出
        for line in text.split("\n"):
            if "駅" in line and len(line) < 20:
                return line.strip()

    except:
        pass

    return "駅情報取得失敗"
