# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from station_search import get_station


def detect_company(url):

    if "indeed" in url:
        return "Indeed"

    if "staffservice" in url:
        return "スタッフサービス"

    if "manpower" in url:
        return "マンパワー"

    if "job-medley" in url:
        return "ジョブメドレー"

    if "mc-nurse" in url:
        return "メディカルコンシェルジュ"

    return "その他"


def build_keywords(station):

    return [
        f"{station} 看護助手 派遣",
        f"{station} 医療事務 派遣",
        f"{station} 病院 派遣",
        f"{station} 看護補助 派遣",
    ]


def search_google(query):

    url = "https://www.google.com/search?q=" + query

    try:
        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5
        )

        soup = BeautifulSoup(r.text, "html.parser")

        links = []

        for a in soup.select("a"):
            href = a.get("href")

            if href and "http" in href:
                links.append(href)

        return links[:10]

    except:
        return []


def score_match(url, station):

    score = 50

    if station in url:
        score += 20

    if "看護" in url:
        score += 10

    if "派遣" in url:
        score += 10

    return f"{score}%"


def search_dispatch_jobs(hospital):

    station = get_station(hospital)

    keywords = build_keywords(station)

    results = []

    for k in keywords:

        links = search_google(k)

        for link in links:

            company = detect_company(link)

            score = score_match(link, station)

            results.append({
                "派遣会社": company,
                "勤務地": station,
                "職種": k,
                "一致度": score,
                "URL": link
            })

    if len(results) == 0:
        results = [{
            "派遣会社": "該当なし",
            "勤務地": station,
            "職種": "派遣求人未検出",
            "一致度": "-",
            "URL": ""
        }]

    return results
