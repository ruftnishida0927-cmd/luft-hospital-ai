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


# =========================
# 厚労省 医療情報提供システム
# =========================

def search_mhlw(name, info):

    url = "https://www.iryou.teikyouseido.mhlw.go.jp/znk-web/juminkanja/S2300/initialize"

    r = fetch(url)

    if not r:
        return info

    # 実際は検索API呼び出しになるが
    # まずはページ取得ベース

    text = r.text

    if name in text:
        info["病院種別"] = "取得成功"

    return info


# =========================
# Wikipedia
# =========================

def search_wikipedia(name, info):

    url = f"https://ja.wikipedia.org/wiki/{name}"

    r = fetch(url)

    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text()

        info = parse_text(text, info)

    return info


# =========================
# Google
# =========================

def search_google(name, info):

    url = f"https://www.google.com/search?q={name}+病院"

    r = fetch(url)

    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text()

        info = parse_text(text, info)

    return info


# =========================
# 病院HP
# =========================

def search_homepage(name, info):

    url = f"https://www.google.com/search?q={name}"

    r = fetch(url)

    if not r:
        return info

    soup = BeautifulSoup(r.text, "html.parser")

    for a in soup.select("a"):

        href = a.get("href")

        if not href:
            continue

        if "http" not in href:
            continue

        if "google" in href:
            continue

        try:
            r2 = fetch(href)

            if r2:
                soup2 = BeautifulSoup(r2.text, "html.parser")
                text = soup2.get_text()

                info = parse_text(text, info)

                break

        except:
            pass

    return info


# =========================
# テキスト解析
# =========================

def parse_text(text, info):

    # 病床数
    if info["病床数"] == "不明":
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
        "皮膚科","泌尿器科","眼科",
        "耳鼻咽喉科","精神科","心療内科"
    ]

    for d in departments:
        if d in text and d not in info["診療科"]:
            info["診療科"].append(d)

    return info


# =========================
# メイン
# =========================

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

    # ① 厚労省
    info = search_mhlw(name, info)

    # ② Wikipedia
    info = search_wikipedia(name, info)

    # ③ 病院HP
    info = search_homepage(name, info)

    # ④ Google
    info = search_google(name, info)

    if len(info["診療科"]) == 0:
        info["診療科"] = ["調査中"]

    return info
