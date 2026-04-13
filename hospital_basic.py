# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup


def fetch(url):
    try:
        return requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8
        )
    except:
        return None


def parse_text(text, info):

    # 病床数
    if info["病床数"] == "不明":
        for line in text.split("\n"):
            if "病床" in line and "床" in line:
                if len(line.strip()) < 40:
                    info["病床数"] = line.strip()
                    break

    # 地域
    for pref in [
        "北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県",
        "茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県",
        "新潟県","富山県","石川県","福井県","山梨県","長野県",
        "岐阜県","静岡県","愛知県","三重県",
        "滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県",
        "鳥取県","島根県","岡山県","広島県","山口県",
        "徳島県","香川県","愛媛県","高知県",
        "福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"
    ]:
        if pref in text:
            info["地域"] = pref

    # 診療科
    departments = [
        "内科","外科","整形外科","小児科",
        "皮膚科","泌尿器科","眼科",
        "耳鼻咽喉科","精神科","心療内科",
        "リハビリテーション科","脳神経外科",
        "循環器内科","消化器内科","呼吸器内科"
    ]

    for d in departments:
        if d in text and d not in info["診療科"]:
            info["診療科"].append(d)

    if "急性期" in text:
        info["急性期"] = True

    if "回復期" in text:
        info["回復期"] = True

    if "療養" in text:
        info["療養"] = True

    return info


def search_query(query, info):

    url = f"https://www.google.com/search?q={query}"

    r = fetch(url)

    if not r:
        return info

    soup = BeautifulSoup(r.text, "html.parser")

    text = soup.get_text()

    info = parse_text(text, info)

    return info


def search_wikipedia(name, info):

    url = f"https://ja.wikipedia.org/wiki/{name}"

    r = fetch(url)

    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text()

        info = parse_text(text, info)

    return info


def get_hospital_basic_info(name):

    info = {
        "病院名": name,
        "病床数": "不明",
        "病院種別": "調査中",
        "地域": "調査中",
        "急性期": False,
        "回復期": False,
        "療養": False,
        "診療科": []
    }

    # ① 医療情報提供制度
    info = search_query(f"{name} 医療情報提供制度", info)

    # ② 病床数
    info = search_query(f"{name} 病床数", info)

    # ③ 病院概要
    info = search_query(f"{name} 病院 概要", info)

    # ④ Wikipedia
    info = search_wikipedia(name, info)

    # ⑤ 一般検索
    info = search_query(f"{name} 病院", info)

    if len(info["診療科"]) == 0:
        info["診療科"] = ["調査中"]

    return info
