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


def fetch(url):
    try:
        return requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8
        )
    except:
        return None


# Wikipedia取得
def search_wikipedia(name):

    url = f"https://ja.wikipedia.org/wiki/{name}"

    r = fetch(url)

    if not r:
        return None

    return r.text


# 公式サイト検索（求人サイト除外）
def search_official_urls(name):

    url = f"https://www.google.com/search?q={name}+病院+公式"

    r = fetch(url)

    if not r:
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    urls = []

    for a in soup.select("a"):

        href = a.get("href")

        if not href:
            continue

        if "http" not in href:
            continue

        # 除外
        if "google" in href:
            continue

        if "job" in href:
            continue

        if "求人" in href:
            continue

        if "townwork" in href:
            continue

        if "indeed" in href:
            continue

        if "rikunabi" in href:
            continue

        urls.append(href)

    return urls[:3]


def build_info(text, name):

    flags = extract_hospital_type_flags(text)

    return {
        "病院名": name,
        "病床数": extract_bed_count(text) or "不明",
        "病院種別": "一般病院",
        "地域": extract_prefecture(text),
        "最寄駅": extract_station(text),
        "急性期": flags["急性期"],
        "回復期": flags["回復期"],
        "療養": flags["療養"],
        "診療科": extract_departments(text) or ["調査中"]
    }


def get_hospital_basic_info(name):

    candidates = []

    # Wikipedia
    wiki = search_wikipedia(name)

    if wiki:
        candidates.append(build_info(wiki, name))

    # 公式サイト
    urls = search_official_urls(name)

    for url in urls:

        r = fetch(url)

        if not r:
            continue

        text = r.text

        candidates.append(build_info(text, name))

    # fallback
    if not candidates:

        return [{
            "病院名": name,
            "病床数": "不明",
            "病院種別": "不明",
            "地域": "不明",
            "最寄駅": "不明",
            "急性期": False,
            "回復期": False,
            "療養": False,
            "診療科": ["調査中"]
        }]

    return candidates
