from __future__ import annotations

from datetime import datetime
from src.search_utils import search_web


def collect_policy_updates() -> list:
    queries = [
        'site:mhlw.go.jp 診療報酬 改定 通知 令和8年',
        'site:mhlw.go.jp 調剤報酬 改定 通知 令和8年',
        'site:mhlw.go.jp 施設基準 通知 令和8年',
        'site:mhlw.go.jp 中医協 総会 診療報酬 令和8年',
    ]
    items = []
    seen = set()
    for query in queries:
        for result in search_web(query, max_results=3):
            key = result["url"]
            if key in seen:
                continue
            seen.add(key)
            items.append(
                {
                    "updated_at": datetime.now().isoformat(timespec="seconds"),
                    "category": "制度更新",
                    "title": result["title"],
                    "summary": result["snippet"],
                    "source_name": "web_search",
                    "source_url": result["url"],
                }
            )
    if not items:
        items.append(
            {
                "updated_at": datetime.now().isoformat(timespec="seconds"),
                "category": "制度更新",
                "title": "制度更新情報を取得できませんでした",
                "summary": "実行環境から外部サイトへ接続できないか、検索結果が取得できませんでした。",
                "source_name": "system",
                "source_url": None,
            }
        )
    return items
