#!/usr/bin/env python3
"""Regenerate sitemap.xml with per-language URLs + hreflang annotations.

After gen_i18n_pages.py creates per-language static pages (de/, temari/de/, ...),
the sitemap must list every language version and annotate each <url> with the full
hreflang cluster (xhtml:link) so Google discovers them and serves the right language
per market. Game index entries also carry image/video extensions.

Usage:  python3 tools/gen_sitemap.py   (writes sitemap.xml)
"""
import os, re, glob, json, datetime, subprocess
from xml.sax.saxutils import escape
import xml.dom.minidom as minidom

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SITE = "https://pixelryu.github.io/"
LANGS = ["en", "ja", "zh", "ko", "hi", "id", "de", "fr", "it", "es", "pt", "ru"]
GAMES = ["kado", "hanko", "okaeri", "shizuku", "senko", "wagashi", "counterparts", "temari", "tatami",
         "bounce-cat", "hoshikari", "hayate", "sumlings", "parcel-pals", "issen", "hotaru",
         "liquid-glow-cosmic", "liquid-glow", "mole-whack"]
TODAY = datetime.date.today().isoformat()

# ゲーム以外のサイトセクション（2026-08 刷新で新設）。すべて12言語ページを持つ。
# EN_ONLY_PAGES は「言語ミラーを持たないページ」用の枠で、現在は空
# （press は 2026-08-14 に12言語化した）。ミラーの無いページをここへ入れないと、
# page_group が存在しない /<slug>/ja/ を sitemap に載せて 404 になる。
I18N_PAGES = ["games", "roblox", "support", "about", "press"]
EN_ONLY_PAGES = []   # press は 2026-08-14 に12言語化して I18N_PAGES へ移した


def existing_lastmods():
    out = {}
    p = os.path.join(ROOT, "sitemap.xml")
    if os.path.exists(p):
        s = open(p, encoding="utf-8").read()
        for m in re.finditer(r"<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>", s):
            out[m.group(1)] = m.group(2)
    return out


PREV = existing_lastmods()


# --- lastmod: when the page's CONTENT actually last changed -------------------
# Previously TODAY was a hardcoded literal, so 247 of 295 URLs all claimed
# "2026-07-10" no matter what had really changed — the freshness signal was dead.
# Stamping everything with today's date instead is just as wrong in the other
# direction (crying wolf costs the whole sitemap's credibility), so the date comes
# from git: the commit that last touched the backing file, or today if the file is
# genuinely being changed in this deploy (dirty/untracked).
def _git_last_change_dates():
    """repo-relative path -> ISO date of the most recent commit touching it."""
    dates = {}
    try:
        p = subprocess.run(
            ["git", "-C", ROOT, "log", "--no-renames", "--date=short",
             "--format=@%cd", "--name-only"],
            capture_output=True, text=True, timeout=300)
        cur = None
        for line in p.stdout.splitlines():
            if line.startswith("@"):
                cur = line[1:]
            elif line and cur and line not in dates:
                dates[line] = cur          # first hit == most recent commit
    except Exception:
        pass
    return dates


def _git_dirty_paths():
    """repo-relative paths with uncommitted changes (modified, added or untracked)."""
    try:
        p = subprocess.run(["git", "-C", ROOT, "status", "--porcelain", "-uall"],
                           capture_output=True, text=True, timeout=300)
        out = set()
        for line in p.stdout.splitlines():
            if len(line) > 3:
                out.add(line[3:].strip().strip('"'))
        return out
    except Exception:
        return set()


GIT_DATES = _git_last_change_dates()
DIRTY = _git_dirty_paths()


def lastmod_for(rel, loc):
    """rel = repo-relative file backing this URL; loc = the URL (for PREV fallback)."""
    if rel and rel in DIRTY:
        return TODAY
    if rel and rel in GIT_DATES:
        return GIT_DATES[rel]
    return PREV.get(loc, TODAY)


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


def page_group(orig, en_priority, slug=None, media=True):
    """Emit en + 11 language <url> entries (hreflang on each); media on the en game index.
    media=False は新設セクション用（og.png 等をゲーム扱いで拾わせない）。"""
    hl = hreflang_xml(orig)
    base = (slug + "/") if slug else ""
    blocks = [url_block(orig, lastmod_for(base + "index.html", orig), en_priority,
                        hl, media_xml(slug) if (slug and media) else "")]
    for l in LANGS:
        if l == "en":
            continue
        loc = orig + l + "/"
        blocks.append(url_block(loc, lastmod_for(base + l + "/index.html", loc), "0.7", hl))
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
    # video.html was previously omitted here even though it ships robots:index,follow,
    # a self-canonical and 17 inbound links from the homepage — i.e. it was crawled but
    # never declared. Declaring it (and giving it VideoObject JSON-LD, see
    # gen_video_pages.py) is what makes the promo videos eligible for video results.
    for sub, pri in [("overview.html", "0.7"), ("video.html", "0.6"),
                     ("privacy_policy.html", "0.3"), ("terms_of_service.html", "0.3")]:
        loc = orig + sub
        if os.path.exists(os.path.join(ROOT, slug, sub)):
            out.append(url_block(loc, lastmod_for(slug + "/" + sub, loc), pri))

# サイトセクション（/games/ /roblox/ /support/ /about/ は12言語、/press/ は英語のみ）
for slug in I18N_PAGES:
    out += page_group(SITE + slug + "/", "0.8", slug=slug, media=False)
for slug, pri in EN_ONLY_PAGES:
    loc = SITE + slug + "/"
    out.append(url_block(loc, lastmod_for(slug + "/index.html", loc), pri))

out.append("</urlset>")
open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(out) + "\n")

d = minidom.parse(os.path.join(ROOT, "sitemap.xml"))
print("urls=%d images=%d videos=%d xhtml:link=%d  (well-formed)" % (
    len(d.getElementsByTagName("url")), len(d.getElementsByTagName("image:image")),
    len(d.getElementsByTagName("video:video")), len(d.getElementsByTagName("xhtml:link"))))
