# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup


def get_hospital_url(name):

    query = f"{name} 病院 公式"
    url = f"https://www.google.com/search?q={query}"

    try:
        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )

        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.select("a"):

            href = a.get("href")

            if not href:
                continue

            if "http" not in href:
                continue

            if "google" in href:
                continue

            if "wikipedia" in href:
                continue

            if "map" in href:
                continue

            return href

    except:
        pass

    return None
