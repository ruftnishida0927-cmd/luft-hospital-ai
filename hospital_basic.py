# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup


def fetch(url):
    try:
        return requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
    except:
        return None


def parse_text(text, info):

    # 病床数
    for line in text.split("\n"):
        if "床" in line and "病床" in line:
            if len(line) < 50:
                info["病床数"] = line.strip()

    # 地域
    prefs = ["京都府","大阪府","兵庫県","滋賀県","奈良県"]

    for p in prefs:
        if p in text:
            info["地域"] = p

    # 診療科
    deps = [
        "内科","外科","整形外科","小児科",
        "皮膚科","泌尿器科","眼科",
        "耳鼻咽喉科","精神科","心療内科",
        "リハビリテーション科"
    ]

    for d in deps:
        if d in text:
            if d not in info["診療科"]:
                info["診療科"].append(d)

    if "急性期" in text:
        info["急性期"] = True

    if "回復期" in text:
        info["回復期"] = True

    if "療養" in text:
        info["療養"] = True

    return info


def search_wikipedia(name, info):

    url = f"https://ja.wikipedia.org/wiki/{name}"

    r = fetch(url)

    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text()
        info = parse_text(text, info)

    return info


def search_by_google_result(name, info):

    url = f"https://www.google.com/search?q={name}+病院"

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

    # Wikipedia
    info = search_wikipedia(name, info)

    # 病院HP
    info = search_by_google_result(name, info)

    if len(info["診療科"]) == 0:
        info["診療科"] = ["調査中"]

    return info
