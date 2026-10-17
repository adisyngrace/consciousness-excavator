"""CORE API v3 client (standalone, philosophy pilot; prompt 09). Responses are cached gzipped under data/core_cache/
(CORE full text stays in gitignored data/). Throttled to 1 request per 2.1 s (free tier: 5 single requests / 10 s)."""
import gzip
import hashlib
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
API = "https://api.core.ac.uk/v3/search/works"
CACHE = ROOT / "data" / "core_cache"
INTERVAL = 2.1
YEARS = "yearPublished>={a} AND yearPublished<={b} AND language.code:\"en\""
_last = 0.0


def _path(params: dict) -> Path:
    return CACHE / (hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest() + ".json.gz")


def search(q: str, limit: int = 100, offset: int = 0) -> dict:
    """Cached search. Raises RuntimeError on persistent failure (callers log and continue)."""
    global _last
    params = {"q": q, "limit": limit, "offset": offset}
    p = _path(params)
    if p.exists():
        return json.loads(gzip.decompress(p.read_bytes()))
    headers = {"Authorization": "Bearer " + os.environ["CORE_API_KEY"],
               "User-Agent": os.getenv("USER_AGENT", "consciousness-excavator/0.1")}
    last_err = ""
    for attempt in range(5):
        wait = INTERVAL - (time.monotonic() - _last)
        if wait > 0:
            time.sleep(wait)
        try:
            r = requests.get(API, params=params, headers=headers, timeout=120)
            _last = time.monotonic()
        except requests.RequestException as e:
            last_err = f"{type(e).__name__}"
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 200:
            CACHE.mkdir(parents=True, exist_ok=True)
            p.write_bytes(gzip.compress(r.content))
            return r.json()
        last_err = f"HTTP {r.status_code}"
        if r.status_code == 429:
            time.sleep(10 * (attempt + 1))
        elif r.status_code < 500:
            break
        else:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"CORE search failed ({last_err}) for q={q[:80]!r} offset={offset}")


def phrase_or(terms: list[str], fields: tuple[str, ...] = ()) -> str:
    """OR of quoted phrases, optionally restricted to fields (e.g. ('title','abstract'))."""
    if not fields:
        return "(" + " OR ".join(f'"{t}"' for t in terms) + ")"
    return "(" + " OR ".join(f'{f}:"{t}"' for t in terms for f in fields) + ")"
