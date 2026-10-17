"""Rate-limited, disk-cached HTTP GET helper."""
import hashlib
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
USER_AGENT = os.getenv("USER_AGENT", "consciousness-excavator/0.1")
DELAY = float(os.getenv("REQUEST_DELAY", "1.0"))

_last_request = 0.0


def _cache_path(url: str, params: dict | None) -> Path:
    key = url + "?" + json.dumps(params or {}, sort_keys=True)
    return CACHE_DIR / (hashlib.sha256(key.encode()).hexdigest() + ".json")


def get(url: str, params: dict | None = None, refresh: bool = False) -> dict:
    """GET with cache. Returns {url, status, content_type, text}. Only cached on HTTP < 500."""
    global _last_request
    path = _cache_path(url, params)
    if path.exists() and not refresh:
        return json.loads(path.read_text())

    wait = DELAY - (time.monotonic() - _last_request)
    if wait > 0:
        time.sleep(wait)
    resp = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=30)
    _last_request = time.monotonic()

    result = {"url": resp.url, "status": resp.status_code,
              "content_type": resp.headers.get("content-type", ""), "text": resp.text}
    if resp.status_code < 500:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result))
    return result
