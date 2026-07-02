#!/usr/bin/env python3
"""Regenerate sitemap.xml with per-language URLs + hreflang annotations.

After gen_i18n_pages.py creates per-language static pages (de/, temari/de/, ...),
the sitemap must list every language version and annotate each <url> with the full
hreflang cluster (xhtml:link) so Google discovers them and serves the right language
per market. Game index entries also carry image/video extensions.

Usage:  python3 tools/gen_sitemap.py   (writes sitemap.xml)
"""
import os, re, glob, json
from xml.sax.saxutils import escape
import xml.dom.minidom as minidom

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SITE = "https://pixelryu.github.io/"
LANGS = ["en", "ja", "zh", "ko", "hi", "id", "de", "fr", "it", "es", "pt", "ru"]
GAMES = ["okaeri", "shizuku", "senko", "wagashi", "counterparts", "temari", "tatami", "bounce-cat",
         "hayate", "sumlings", "parcel-pals", "issen", "hotaru", "liquid-glow-cosmic",
         "liquid-glow", "mole-whack"]
TODAY = "2026-06-28"


def existing_lastmods():
    out = {}
    p = os.path.join(ROOT, "sitemap.xml")
    if os.path.exists(p):
        s = open(p, encoding="utf-8").read()
        for m in re.finditer(r"<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>", s):
            out[m.group(1)] = m.group(2)
    return out


PREV = existing_lastmods()


def media_xml(slug):
    imgs = []
    for f in ["og.png", "icon.png"]:
        if os.path.exists(os.path.join(ROOT, slug, f)):
            imgs.append(f)
    for f in sorted(glob.glob(os.path.join(ROOT, slug, "screenshots", "*"))):
        imgs.append("screenshots/" + os.path.basename(f))
    for f in sorted(glob.glob(os.path.join(ROOT, slug, "key_*"))):
        imgs.append(os.path.basename(f))
    src = open(os.path.join(ROOT, slug, "index.html"), encoding="utf-8").read()
    vids = []
    for m in re.finditer(r'<script type="application/ld\+json">(.+?)</script>', src, re.S):
        o = json.loads(m.group(1))
        for oo in (o if isinstance(o, list) else [o]):
            if oo.get("@type") == "VideoObject":
                vids.append(oo)
    rows = []
    for img in imgs:
        rows.append("    <image:image>\n      <image:loc>%s%s/%s</image:loc>\n    </image:image>" % (SITE, slug, img))
    for v in vids:
        date = v.get("uploadDate", "")
        if re.match(r"^\d{4}-\d{2}-\d{2}T", date):
            # already a full W3C datetime (e.g. 2026-05-23T00:00:00+00:00) — emit as-is
            pub = "\n      <video:publication_date>%s</video:publication_date>" % date
        elif re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            # date-only — append midnight UTC to satisfy the video sitemap datetime format
            pub = "\n      <video:publication_date>%sT00:00:00+00:00</video:publication_date>" % date
        else:
            pub = ""
        rows.append(
            "    <video:video>\n"
            "      <video:thumbnail_loc>%s</video:thumbnail_loc>\n"
            "      <video:title>%s</video:title>\n"
            "      <video:description>%s</video:description>\n"
            "      <video:content_loc>%s</video:content_loc>%s\n"
            "      <video:family_friendly>yes</video:family_friendly>\n"
            "    </video:video>" % (
                escape(v.get("thumbnailUrl", "")), escape(v.get("name", ""))[:100],
                escape((v.get("description", "") or "")[:2040]), escape(v.get("contentUrl", "")), pub))
    return "\n".join(rows)


def hreflang_xml(orig):
    rows = []
    for l in LANGS:
        href = orig + (l + "/" if l != "en" else "")
        rows.append('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (l, href))
    rows.append('    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>' % orig)
    return "\n".join(rows)


def url_block(loc, lastmod, priority, hreflang="", media=""):
    parts = ["  <url>", "    <loc>%s</loc>" % loc, "    <lastmod>%s</lastmod>" % lastmod,
             "    <changefreq>monthly</changefreq>", "    <priority>%s</priority>" % priority]
    if hreflang:
        parts.append(hreflang)
    if media:
        parts.append(media)
    parts.append("  </url>")
    return "\n".join(parts)


def page_group(orig, en_priority, slug=None):
    """Emit en + 11 language <url> entries (hreflang on each); media on the en game index."""
    hl = hreflang_xml(orig)
    blocks = [url_block(orig, TODAY, en_priority, hl, media_xml(slug) if slug else "")]
    for l in LANGS:
        if l == "en":
            continue
        blocks.append(url_block(orig + l + "/", TODAY, "0.7", hl))
    return blocks


out = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
       '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"',
       '        xmlns:video="http://www.google.com/schemas/sitemap-video/1.1"',
       '        xmlns:xhtml="http://www.w3.org/1999/xhtml">']

# homepage group (en + 11 langs)
out += page_group(SITE, "1.0")

# each game: index group (en + 11 langs, media on en) + en-only sub pages
for slug in GAMES:
    orig = SITE + slug + "/"
    out += page_group(orig, "0.9", slug=slug)
    for sub, pri in [("overview.html", "0.7"), ("privacy_policy.html", "0.3"), ("terms_of_service.html", "0.3")]:
        loc = orig + sub
        if os.path.exists(os.path.join(ROOT, slug, sub)):
            out.append(url_block(loc, PREV.get(loc, TODAY), pri))

out.append("</urlset>")
open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(out) + "\n")

d = minidom.parse(os.path.join(ROOT, "sitemap.xml"))
print("urls=%d images=%d videos=%d xhtml:link=%d  (well-formed)" % (
    len(d.getElementsByTagName("url")), len(d.getElementsByTagName("image:image")),
    len(d.getElementsByTagName("video:video")), len(d.getElementsByTagName("xhtml:link"))))
