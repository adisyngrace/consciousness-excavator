"""Europe PMC client: cursor-paged search (cached) and threaded, throttled full-text XML download."""
import gzip
import json
import os
import threading
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from src import http

load_dotenv()
REST = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
XML_DIR = Path(__file__).resolve().parents[2] / "data" / "xml"
UA = {"User-Agent": os.getenv("USER_AGENT", "consciousness-excavator/0.1")}
SEARCH_DELAY = 0.25        # seconds between (cached-on-disk) search page requests
FETCH_INTERVAL = 0.25      # global minimum gap between XML requests across all workers (~4 req/s)
MAX_ENUMERATE = 60000


def _search_page(params: dict, cache: bool) -> dict:
    if cache:
        r = http.get(REST + "search", params=params)
        status, text = r["status"], r["text"]
    else:                      # uncached: used for huge enumerations whose pages we do not want on disk
        for attempt in range(4):
            _throttle()
            try:
                resp = requests.get(REST + "search", params=params, headers=UA, timeout=90)
                status, text = resp.status_code, resp.text
                if status < 500:
                    break
            except requests.RequestException:
                status, text = 0, ""
            time.sleep(2 ** attempt)
    if status != 200:
        raise RuntimeError(f"search HTTP {status} for {params['query'][:80]}")
    return json.loads(text)


def search_all(query: str, max_enumerate: int = MAX_ENUMERATE, cache: bool = True) -> tuple[int, list[dict]]:
    """Return (total hit count, lite records that have a PMCID) by cursor paging, up to max_enumerate."""
    http.DELAY = SEARCH_DELAY
    out, cursor, total = [], "*", 0
    while True:
        j = _search_page({"query": query, "format": "json", "resultType": "lite", "pageSize": 1000,
                          "cursorMark": cursor}, cache)
        total = j["hitCount"]
        out += [x for x in j["resultList"]["result"] if x.get("pmcid")]
        nxt = j.get("nextCursorMark")
        if not nxt or nxt == cursor or not j["resultList"]["result"] or len(out) >= max_enumerate:
            return total, out
        cursor = nxt


_lock = threading.Lock()
_next_ok = 0.0


S3 = "https://pmc-oa-opendata.s3.amazonaws.com"   # PMC OA open-data bucket: no per-client throttling
S3_INTERVAL = 0.05


def _throttle(interval: float = FETCH_INTERVAL) -> None:
    global _next_ok
    with _lock:
        now = time.monotonic()
        wait = _next_ok - now
        _next_ok = max(now, _next_ok) + interval
    if wait > 0:
        time.sleep(wait)


def xml_path(pmcid: str) -> Path:
    return XML_DIR / f"{pmcid}.xml.gz"


def _fetch_s3(pmcid: str, path: Path) -> bool:
    """First choice: the AWS PMC open-data copy (version .1). False -> caller falls back to Europe PMC."""
    for _ in range(2):
        _throttle(S3_INTERVAL)
        try:
            r = requests.get(f"{S3}/{pmcid}.1/{pmcid}.1.xml", headers=UA, timeout=30)
        except requests.RequestException:
            continue
        if r.status_code == 200 and b"<article" in r.content:
            tmp = path.with_suffix(".tmp")
            tmp.write_bytes(gzip.compress(r.content))
            tmp.replace(path)
            return True
        if r.status_code in (403, 404):
            return False
    return False


def fetch_xml(pmcid: str, retries: int = 4) -> tuple[bool, str | None, str | None]:
    """Download one article's JATS XML to data/xml. Returns (ok, error, source). Skips files already on disk
    (those predate the S3 route, so they are Europe PMC copies)."""
    path = xml_path(pmcid)
    if path.exists():
        return True, None, "europepmc"
    XML_DIR.mkdir(parents=True, exist_ok=True)
    if _fetch_s3(pmcid, path):
        return True, None, "s3"
    err = None
    for attempt in range(retries):
        _throttle()
        try:
            r = requests.get(f"{REST}{pmcid}/fullTextXML", headers=UA, timeout=30)
        except requests.RequestException as e:
            err = f"network: {type(e).__name__}"
        else:
            if r.status_code == 200 and b"<article" in r.content:
                tmp = path.with_suffix(".tmp")
                tmp.write_bytes(gzip.compress(r.content))
                tmp.replace(path)
                return True, None, "europepmc"
            if r.status_code in (404, 403, 410):
                return False, f"HTTP {r.status_code}: full text not available", None
            err = f"HTTP {r.status_code}" if r.status_code != 200 else "200 but no <article> in body"
        time.sleep(2 ** attempt)
    return False, f"gave up after {retries} tries: {err}", None


def read_xml(pmcid: str) -> bytes:
    return gzip.decompress(xml_path(pmcid).read_bytes())
