# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup

from extractors import (
    extract_prefecture,
    extract_station,
    extract_bed_count
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


# -------------------------
# Google検索
# -------------------------

def search_google(name):

    url = f"https://www.google.com/search?q={name}+病院"

    r = fetch(url)

    if not r:
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    results = []

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

            if not r2:
                continue

            text = BeautifulSoup(
                r2.text,
                "html.parser"
            ).get_text()

            info = {
                "住所": text[:300],
                "地域": extract_prefecture(text),
                "最寄駅": extract_station(text),
                "病床数": extract_bed_count(text),
                "source": "google"
            }

            results.append(info)

        except:
            pass

    return results[:3]


# -------------------------
# Wikipedia
# -------------------------

def search_wikipedia(name):

    url = f"https://ja.wikipedia.org/wiki/{name}"

    r = fetch(url)

    if not r:
        return []

    text = BeautifulSoup(
        r.text,
        "html.parser"
    ).get_text()

    return [{
        "住所": text[:300],
        "地域": extract_prefecture(text),
        "最寄駅": extract_station(text),
        "病床数": extract_bed_count(text),
        "source": "wiki"
    }]


# -------------------------
# 厚労省
# -------------------------

def search_mhlw(name):

    url = "https://www.iryou.teikyouseido.mhlw.go.jp/"

    r = fetch(url)

    if not r:
        return []

    text = BeautifulSoup(
        r.text,
        "html.parser"
    ).get_text()

    return [{
        "住所": text[:300],
        "地域": extract_prefecture(text),
        "最寄駅": extract_station(text),
        "病床数": extract_bed_count(text),
        "source": "mhlw"
    }]
