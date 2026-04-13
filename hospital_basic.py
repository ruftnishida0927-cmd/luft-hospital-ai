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


def search_official_urls(name):

    url = f"https://www.google.com/search?q={name}+病院"

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

    urls = search_official_urls(name)

    candidates = []

    for url in urls:

        r = fetch(url)

        if not r:
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text()

        info = build_info(text, name)

        candidates.append(info)

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
