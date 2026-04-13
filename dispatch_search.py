# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from station_search import get_station


def search_dispatch_jobs(hospital):

    station = get_station(hospital)

    keywords = [
        "看護助手 派遣",
        "医療事務 派遣",
        "病院 派遣",
        "看護補助 派遣"
    ]

    base = "https://www.google.com/search?q="

    results = []

    for k in keywords:

        query = f"{station} {k}"
        url = base + query

        try:
            r = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=5
            )

            soup = BeautifulSoup(r.text, "html.parser")

            links = soup.select("a")

            for l in links[:10]:

                href = l.get("href")

                if href and "http" in href:

                    results.append({
                        "派遣会社": "検索候補",
                        "勤務地": station,
                        "職種": k,
                        "一致度": "候補",
                        "URL": href
                    })

        except:
            pass

    if len(results) == 0:
        results = [{
            "派遣会社": "該当なし",
            "勤務地": station,
            "職種": "派遣求人未検出",
            "一致度": "-",
            "URL": ""
        }]

    return results
