# -*- coding: utf-8 -*-
import json
import os
import time

CACHE_FILE = "search_cache.json"
CACHE_TTL_SECONDS = 60 * 60 * 24  # 24時間


def _load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def _save_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except:
        pass


def get_cached(key):
    cache = _load_cache()

    if key not in cache:
        return None

    item = cache[key]
    ts = item.get("timestamp", 0)

    if time.time() - ts > CACHE_TTL_SECONDS:
        return None

    return item.get("data")


def set_cached(key, data):
    cache = _load_cache()
    cache[key] = {
        "timestamp": time.time(),
        "data": data
    }
    _save_cache(cache)
