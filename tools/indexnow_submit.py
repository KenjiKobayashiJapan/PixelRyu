#!/usr/bin/env python3
"""Submit all sitemap URLs to IndexNow (Bing / Yandex / Seznam / Naver).

Usage:
    python3 tools/indexnow_submit.py            # submit every <loc> in sitemap.xml
    python3 tools/indexnow_submit.py URL [URL…] # submit specific URLs only

Run AFTER the site (including the key file at the repo root) is deployed to
GitHub Pages — the endpoint verifies https://pixelryu.github.io/<KEY>.txt.
Exit codes: 0 = accepted (200/202), 1 = other.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

HOST = "pixelryu.github.io"
ROOT = Path(__file__).resolve().parent.parent
ENDPOINT = "https://api.indexnow.org/indexnow"


def find_key():
    keys = [p for p in ROOT.glob("*.txt")
            if re.fullmatch(r"[0-9a-f]{32}", p.stem) and p.read_text().strip() == p.stem]
    if len(keys) != 1:
        sys.exit("IndexNow key file not found (expected exactly one <32-hex>.txt at repo root)")
    return keys[0].stem


def sitemap_urls():
    xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    # <loc> of <url> entries only (video:/image: sub-elements use different tags)
    return re.findall(r"<loc>([^<]+)</loc>", xml)


def main():
    key = find_key()
    urls = sys.argv[1:] or sitemap_urls()
    if not urls:
        sys.exit("no URLs to submit")
    payload = {
        "host": HOST,
        "key": key,
        "keyLocation": f"https://{HOST}/{key}.txt",
        "urlList": urls[:10000],
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req) as res:
            print(f"IndexNow: HTTP {res.status} — submitted {len(payload['urlList'])} URLs")
    except urllib.error.HTTPError as e:
        print(f"IndexNow: HTTP {e.code} — {e.read().decode('utf-8', 'replace')[:300]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
