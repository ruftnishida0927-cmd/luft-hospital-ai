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
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Connection": "keep-alive"
            },
            timeout=10
        )
    except:
        return None


def search_wikipedia(name):
    url = f"https://ja.wikipedia.org/wiki/{name}"
    r = fetch(url)

    if not r:
        return None

    return r.text


def search_official_urls(name):
    query = f"{name} 病院 公式"
    url = f"https://www.google.com/search?q={query}&hl=ja&num=10"

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
        if "youtube" in href:
            continue
        if "indeed" in href:
            continue
        if "townwork" in href:
            continue
        if "rikunabi" in href:
            continue
        if "job-medley" in href:
            continue
        if "staffservice" in href:
            continue
        if "manpower" in href:
            continue

        urls.append(href)

    # 重複除去
    deduped = []
    for u in urls:
        if u not in deduped:
            deduped.append(u)

    return deduped[:5]


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

    # ① Wikipedia
    wiki = search_wikipedia(name)
    if wiki:
        candidates.append(build_info(wiki, name))

    # ② 公式サイト候補
    urls = search_official_urls(name)

    for url in urls:
        r = fetch(url)

        if not r:
            continue

        text = r.text
        candidates.append(build_info(text, name))

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
