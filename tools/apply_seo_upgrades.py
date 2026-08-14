#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apply_seo_upgrades.py — 2026-08 刷新の SEO 施策を全ゲームページへ冪等に適用する。

  1) Smart App Banner: iOS 公開済みのページに <meta name="apple-itunes-app">
     （Safari から1タップで App Store へ送る。iOS 公開済みのページだけ）
  2) VideoGame JSON-LD のマルチタイプ化:
     "@type":"VideoGame" → ["VideoGame","MobileApplication"]
     Google 公式: VideoGame 単体タイプにはリッチリザルトを出さない。
     併せて applicationCategory:"GameApplication" を持たせる。

いずれも「実際に live なストアリンクがそのページにあるか」を根拠にする（★正直ルール）。
使い方: python3 tools/apply_seo_upgrades.py
"""
import os
import re
import json
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANG_DIRS = {"ja", "zh", "ko", "hi", "id", "de", "fr", "it", "es", "pt", "ru"}
SKIP = {"games", "roblox", "support", "about", "press"}   # ゲームでないセクション


def game_slugs():
    out = []
    for name in sorted(os.listdir(BASE)):
        p = os.path.join(BASE, name, "index.html")
        if name in LANG_DIRS or name in SKIP or name.startswith("."):
            continue
        if os.path.isdir(os.path.join(BASE, name)) and os.path.exists(p):
            out.append(name)
    return out


def hero_ios_id(html):
    """hero-badges の中にある（＝実際に押せる）App Store リンクの Apple ID。"""
    m = re.search(r'<section class="hero-badges.*?</section>', html, re.S)
    if not m:
        return None
    mm = re.search(r'apps\.apple\.com/app/id(\d+)', m.group(0))
    return mm.group(1) if mm else None


def add_smart_banner(html, app_id):
    tag = f'<meta name="apple-itunes-app" content="app-id={app_id}">'
    if 'name="apple-itunes-app"' in html:
        return re.sub(r'<meta name="apple-itunes-app"[^>]*>', tag, html, count=1), False
    anchor = "<!-- SEO/LLMO start (managed) -->"
    if anchor not in html:
        return html, False
    return html.replace(anchor, anchor + "\n" + tag, 1), True


def multitype_videogame(html):
    """VideoGame JSON-LD をマルチタイプへ。JSON を壊さないよう部分置換で行う。"""
    changed = False

    def repl(m):
        nonlocal changed
        body = m.group(1)
        if '"@type":"VideoGame"' not in body and '"@type": "VideoGame"' not in body:
            return m.group(0)
        try:
            obj = json.loads(body)
        except Exception:
            return m.group(0)
        items = obj if isinstance(obj, list) else [obj]
        touched = False
        for o in items:
            if o.get("@type") == "VideoGame":
                o["@type"] = ["VideoGame", "MobileApplication"]
                o.setdefault("applicationCategory", "GameApplication")
                touched = True
        if not touched:
            return m.group(0)
        changed = True
        return '<script type="application/ld+json">%s</script>' % json.dumps(
            obj, ensure_ascii=False, separators=(",", ":"))

    out = re.sub(r'<script type="application/ld\+json">(.+?)</script>', repl, html, flags=re.S)
    return out, changed


def main():
    banners = []
    types = []
    for slug in game_slugs():
        path = os.path.join(BASE, slug, "index.html")
        html = open(path, encoding="utf-8").read()
        orig = html

        app_id = hero_ios_id(html)
        if app_id:
            html, added = add_smart_banner(html, app_id)
            if added:
                banners.append(f"{slug} (id{app_id})")

        html, t = multitype_videogame(html)
        if t:
            types.append(slug)

        if html != orig:
            open(path, "w", encoding="utf-8").write(html)

    print(f"Smart App Banner を追加: {len(banners)} ページ")
    for b in banners:
        print("   ", b)
    print(f"JSON-LD をマルチタイプ化: {len(types)} ページ")
    print("   ", ", ".join(types))


if __name__ == "__main__":
    main()
