# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup

from extractors import build_job_features
from match_engine import build_match_result


def fetch(url):
    try:
        return requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
    except:
        return None


def search_google_links(query):

    url = f"https://www.google.com/search?q={query}"

    r = fetch(url)

    if not r:
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    links = []

    for a in soup.select("a"):
        href = a.get("href")

        if not href:
            continue

        if "http" not in href:
            continue

        if "google" in href:
            continue

        if "youtube" in href:
            continue

        links.append(href)

    return links[:2]


def extract_page_text(url):

    r = fetch(url)

    if not r:
        return ""

    soup = BeautifulSoup(r.text, "html.parser")

    return soup.get_text()


def search_dispatch_jobs(hospital_info):

    name = hospital_info["病院名"]

    queries = [
        f"{name} 看護助手 派遣",
        f"{name} 医療事務 派遣",
        f"{name} 看護補助 派遣",
        f"{name} 病院 派遣 非公開",
        f"{name} 無資格 病院 派遣",
    ]

    results = []

    for query in queries:

        links = search_google_links(query)

        for link in links:

            try:
                text = extract_page_text(link)

                if not text:
                    continue

                job_features = build_job_features(text)

                match = build_match_result(
                    hospital_info,
                    job_features
                )

                results.append({
                    "URL": link,
                    "一致率": match["一致率"],
                    "判定": match["判定"],
                    "根拠": " / ".join(match["根拠"]),
                    "最寄駅": job_features["最寄駅"],
                    "徒歩": job_features["徒歩分数"],
                    "地域": job_features["地域"],
                    "職種": ",".join(job_features["職種キーワード"])
                })

            except:
                pass

    results.sort(
        key=lambda x: x["一致率"],
        reverse=True
    )

    return results[:2]
