#!/usr/bin/env python3
"""Pre-deploy sanity checks for the PixelRyu site (run before every push).

It exists to stop the #1 deploy regression we have actually hit:
a sub-page whose app slug is NOT registered in breadcrumb.js APP_NAMES,
which makes breadcrumb.js bail out (detect() -> null) and render NO
breadcrumb at all — silently. See DEPLOY.md.

Checks
  1. breadcrumb: every app sub-page that includes breadcrumb.js must have
     its slug registered in breadcrumb.js APP_NAMES (else breadcrumb is
     missing on that page).                                      -> ERROR
  2. breadcrumb: pages of a registered app that forgot the include. -> WARN
  3. cache: every breadcrumb.js / video reference carries a ?v=.    -> WARN

Usage:  python3 tools/check_site.py          (from the PixelRyu repo root)
Exit code 1 if any ERROR, else 0.
"""
import glob
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def rel(path):
    return os.path.relpath(path, ROOT)


errors, warns = [], []

# Slugs registered in breadcrumb.js APP_NAMES (e.g. "tatami": { all: "TATAMI" }).
breadcrumb = read(os.path.join(ROOT, "breadcrumb.js"))
registered = set(re.findall(r'"([a-z0-9-]+)":\s*\{\s*all:', breadcrumb))

# Every directory one level below the root that has an index.html is an app page.
app_dirs = sorted({os.path.dirname(p) for p in glob.glob(os.path.join(ROOT, "*", "index.html"))})

for d in app_dirs:
    slug = os.path.basename(d)
    pages = sorted(glob.glob(os.path.join(d, "*.html")))
    with_bc = [p for p in pages if "breadcrumb.js" in read(p)]
    without_bc = [p for p in pages if "breadcrumb.js" not in read(p)]

    # (1) breadcrumb present in markup but slug not registered -> renders nothing.
    if with_bc and slug not in registered:
        errors.append(
            "[breadcrumb] app '%s' is NOT in breadcrumb.js APP_NAMES -> breadcrumb will NOT render on: %s"
            % (slug, ", ".join(rel(p) for p in with_bc))
        )

    # (2) a registered app whose some pages forgot the include.
    if slug in registered and without_bc:
        warns.append(
            "[breadcrumb] app '%s' pages missing the breadcrumb.js <script>: %s"
            % (slug, ", ".join(rel(p) for p in without_bc))
        )

    # (3) cache-busting: breadcrumb.js / .mp4 refs should all carry ?v=.
    for p in pages:
        html = read(p)
        for m in re.finditer(r'(breadcrumb\.js|[\w./-]+\.mp4)(\?v=\d+)?', html):
            if m.group(1).endswith((".js", ".mp4")) and not m.group(2):
                warns.append("[cache] %s references %s without ?v=" % (rel(p), m.group(1)))

# ---------------------------------------------------------------------------
# SEO/LLMO completeness checks (added 2026-06-11 — each one is a regression we
# actually shipped: TATAMI missing from sitemap+llms, hotaru/liquid-glow static
# <head> left as "Legal" copy that JS-less AI crawlers ingested).
# ---------------------------------------------------------------------------
import html as _html
import json as _json

# (4) sitemap completeness: every app page file must be listed in sitemap.xml.
sitemap = read(os.path.join(ROOT, "sitemap.xml"))
for d in app_dirs:
    slug = os.path.basename(d)
    for page in ("index.html", "overview.html", "privacy_policy.html", "terms_of_service.html"):
        if not os.path.exists(os.path.join(d, page)):
            continue
        url = "https://pixelryu.github.io/%s/" % slug
        if page != "index.html":
            url += page
        if "<loc>%s</loc>" % url not in sitemap:
            errors.append("[sitemap] %s missing from sitemap.xml" % url)

# (5) llms.txt completeness: every app must be mentioned at least once.
llms = read(os.path.join(ROOT, "llms.txt"))
for d in app_dirs:
    slug = os.path.basename(d)
    if "/%s/" % slug not in llms:
        errors.append("[llms] app '%s' not mentioned in llms.txt" % slug)


def _norm(s):
    return re.sub(r"\s+", " ", _html.unescape(s)).strip() if s else s


def _en_value(src, key):
    m = re.search(r'\ben\s*:\s*\{|"en"\s*:\s*\{', src)
    if not m:
        return None
    block = src[m.end(): m.end() + 20000]
    km = re.search(r'(?<![\w_"])"?%s"?\s*:\s*"((?:[^"\\]|\\.)*)"' % re.escape(key), block)
    return km.group(1).replace('\\"', '"') if km else None

# (6) static <head> vs en-i18n drift: JS-less crawlers (GPTBot/ClaudeBot/SNS
#     scrapers) read the static values, so they must equal the en i18n strings.
for d in app_dirs + [ROOT]:
    p = os.path.join(d, "index.html")
    src = read(p)
    tm = re.search(r"<title[^>]*>([^<]*)</title>", src)
    dm = re.search(r'<meta name="description"[^>]*content="([^"]*)"', src)
    for key, got in (("title", tm and tm.group(1)), ("meta_desc", dm and dm.group(1))):
        want = _en_value(src, key)
        if want and got and _norm(got) != _norm(want):
            errors.append("[head-drift] %s: static %s differs from en i18n (%r != %r)"
                          % (rel(p), key, _norm(got)[:60], _norm(want)[:60]))

# (7) every ld+json block must parse; (8) game pages should declare free offers.
for p in sorted(glob.glob(os.path.join(ROOT, "*", "*.html"))) + [os.path.join(ROOT, "index.html")]:
    src = read(p)
    for i, m in enumerate(re.finditer(r'<script type="application/ld\+json">(.*?)</script>', src, re.S)):
        try:
            obj = _json.loads(m.group(1))
        except Exception as e:
            errors.append("[jsonld] %s block %d is invalid JSON: %s" % (rel(p), i, e))
            continue
        for o in (obj if isinstance(obj, list) else [obj]):
            if isinstance(o, dict) and o.get("@type") == "VideoGame" and "name" in o and "offers" not in o:
                warns.append("[jsonld] %s: VideoGame without free offers (price 0)" % rel(p))

if warns:
    print("\n".join("WARN  " + w for w in sorted(set(warns))))
if errors:
    print("\n".join("ERROR " + e for e in errors))

print("\n%d app page(s) checked. Registered in breadcrumb.js: %s" % (len(app_dirs), ", ".join(sorted(registered))))
if errors:
    print("\nFAIL: %d error(s) — fix before deploying." % len(errors))
    sys.exit(1)
print("\nOK: breadcrumb / sitemap / llms / head / json-ld are consistent.")
