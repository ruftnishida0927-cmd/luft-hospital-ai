# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup


def get_hospital_basic_info(name):

    info = {
        "病院名": name,
        "病床数": "不明",
        "病院種別": "不明",
        "地域": "不明",
        "急性期": False,
        "回復期": False,
        "療養": False,
        "診療科": []
    }

    try:
        url = f"https://www.google.com/search?q={name}"

        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5
        )

        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text()

        # 病床数
        for line in text.split("\n"):
            if "床" in line and "病床" in line:
                info["病床数"] = line.strip()
                break

        # 地域
        for pref in ["京都府","大阪府","兵庫県","滋賀県","奈良県"]:
            if pref in text:
                info["地域"] = pref

        # 診療科
        departments = [
            "内科","外科","整形外科","小児科",
            "皮膚科","泌尿器科","眼科","耳鼻咽喉科"
        ]

        for d in departments:
            if d in text:
                info["診療科"].append(d)

        if "急性期" in text:
            info["急性期"] = True

        if "回復期" in text:
            info["回復期"] = True

        if "療養" in text:
            info["療養"] = True

    except:
        pass

    return info
