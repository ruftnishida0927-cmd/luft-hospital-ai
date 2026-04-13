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
            timeout=10
        )
    except:
        return None


def search_official_urls(name):

    query = f"{name} 病院"
    url = f"https://www.google.com/search?q={query}"

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

        if "google" in href:
            continue

        if "map" in href:
            continue

        urls.append(href)

    return urls[:5]


def extract_hospital_info(text, name):

    beds = extract_bed_count(text)
    station = extract_station(text)
    region = extract_prefecture(text)
    deps = extract_departments(text)
    flags = extract_hospital_type_flags(text)

    return {
        "病院名": name,
        "病床数": beds if beds else "不明",
        "病院種別": "一般病院",
        "地域": region,
        "最寄駅": station,
        "急性期": flags["急性期"],
        "回復期": flags["回復期"],
        "療養": flags["療養"],
        "診療科": deps if deps else ["調査中"]
    }


def get_hospital_basic_info(name):

    urls = search_official_urls(name)

    candidates = []

    for url in urls:

        r = fetch(url)

        if not r:
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text()

        info = extract_hospital_info(text, name)

        candidates.append(info)

    if not candidates:
        return {
            "病院名": name,
            "病床数": "不明",
            "病院種別": "調査中",
            "地域": "不明",
            "最寄駅": "不明",
            "急性期": False,
            "回復期": False,
            "療養": False,
            "診療科": ["調査中"]
        }

    # とりあえず最初返す（後で一致率で選ぶ）
    return candidates
