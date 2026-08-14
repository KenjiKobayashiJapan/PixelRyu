#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apply_shell.py — PixelRyu 共通シェル（ヘッダー / フッター / site.css / site.js）を
全ページへ冪等に適用する。

設計方針（2026-08 サイト刷新 v1.1）:
  * 19本のゲームページは構造が5パターンに分裂しているため、HTML の書き換えは
    「19/19 で必ず存在する安全なアンカー」だけに限定する。
      - <body> 直後          → skip-link + グローバルヘッダー
      - </body> 直前         → グローバルフッター + site.js
      - </head> 直前         → site.css
      - <div class="container"> → id/role の付与（ゲームページのみ）
  * 既存のインライン <style> は残す。site.css を後から読ませて同詳細度の後勝ちで上書きする。
  * 挿入部は必ずマーカーで囲み、再実行時は置換する（冪等）。
  * シェルの文言は **ページ側の i18n 辞書とは完全に分離**し、`data-pr-i18n` 属性 ＋
    tools/shell_i18n.py（12言語の正本）で扱う。ページ辞書へ機械挿入するのは
    書式4通り（3本は完全ミニファイ）で危険なため。
      - 実行時の切替 … 本スクリプトが生成する assets/shell-i18n.js を site.js が適用
      - 静的な焼込み … gen_i18n_pages.py が言語ミラーへ直接書き込む（AIクローラは JS 非実行）

使い方:
  python3 tools/apply_shell.py            # 全ページ
  python3 tools/apply_shell.py temari     # 個別
"""
import os
import re
import sys
import json
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shell_i18n import SHELL, check as shell_i18n_check   # noqa: E402
# 言語ミラーを持つページの正本。press は英語のみ＝ミラーが無いので、
# そのフッターの言語リンクは自ページ配下ではなくサイト直下の言語版へ向ける
# （向けないと ../press/ja/ という存在しない URL を12本並べることになる）。
from gen_i18n_pages import GAMES as _MG, PAGES as _MP   # noqa: E402
MIRRORED = set(_MG) | set(_MP)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 生成物である言語ディレクトリ（ここは直接編集しない。gen_i18n_pages.py が作る）
LANG_DIRS = {"ja", "zh", "ko", "hi", "id", "de", "fr", "it", "es", "pt", "ru"}

# 新着順（トップの ItemList と同順）。フッターのゲーム一覧に使う。
# 18件（19 slug のうち liquid-glow 旧ページは載せない）＝ tools/gen_pages.py の
# extract_games() と同じ方針。理由はそちらの docstring を参照。
GAMES = [
    ("kado", "KADŌ"),
    ("hanko", "HANKO"),
    ("hoshikari", "Hoshikari"),
    ("okaeri", "Okaeri"),
    ("shizuku", "Shizuku"),
    ("senko", "SENKO"),
    ("wagashi", "WAGASHI"),
    ("counterparts", "CounterParts"),
    ("tatami", "TATAMI"),
    ("temari", "TEMARI"),
    ("bounce-cat", "Bounce Cat"),
    ("hayate", "HAYATE"),
    ("sumlings", "Sumlings"),
    ("parcel-pals", "Parcel Pals"),
    ("issen", "ISSEN"),
    ("hotaru", "HOTARU"),
    ("liquid-glow-cosmic", "Liquid Glow"),
    ("mole-whack", "Mole Whack"),
]

LANGS = [
    ("en", "English", ""), ("ja", "日本語", "ja/"), ("zh", "中文", "zh/"),
    ("ko", "한국어", "ko/"), ("hi", "हिन्दी", "hi/"), ("id", "Indonesia", "id/"),
    ("de", "Deutsch", "de/"), ("fr", "Français", "fr/"), ("it", "Italiano", "it/"),
    ("es", "Español", "es/"), ("pt", "Português", "pt/"), ("ru", "Русский", "ru/"),
]

SOCIAL_ICONS = {
    'Substack': ('https://substack.com/@pixelryu',
     '<svg viewBox="0 0 24 24"><path d="M22.539 8.242H1.46V5.406h21.08v2.836zM1.46 10.812V24L12 18.11 22.54 24V10.812H1.46zM22.54 0H1.46v2.836h21.08V0z"/></svg>'),
    'note': ('https://note.com/pixelryu',
     '<svg viewBox="129 129 234 234"><path d="m139.57,142.06c41.19,0,97.6-2.09,138.1-1.04,54.34,1.39,74.76,25.06,75.45,83.53.69,33.06,0,127.73,0,127.73h-58.79c0-82.83.35-96.5,0-122.6-.69-22.97-7.25-33.92-24.9-36.01-18.69-2.09-71.07-.35-71.07-.35v158.96h-58.79v-210.22Z" fill="currentColor"/></svg>'),
    'YouTube': ('https://www.youtube.com/@PixelRyu-Japan',
     '<svg viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>'),
    'X': ('https://x.com/PixelRyu10752',
     '<svg viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>'),
    'Instagram': ('https://www.instagram.com/pixelryu/',
     '<svg viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>'),
    'Facebook': ('https://www.facebook.com/PixelRyuJapan',
     '<svg viewBox="0 0 24 24"><path d="M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z"/></svg>'),
    'TikTok': ('https://www.tiktok.com/@pixelryu_japan',
     '<svg viewBox="0 0 24 24"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.08-.14 1.62.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/></svg>'),
    'Threads': ('https://www.threads.com/@pixelryu',
     '<svg viewBox="0 0 24 24"><path d="M12.186 24h-.007c-3.581-.024-6.334-1.205-8.184-3.509C2.35 18.44 1.5 15.586 1.472 12.01v-.017c.03-3.579.879-6.43 2.525-8.482C5.845 1.205 8.6.024 12.18 0h.014c2.746.02 5.043.725 6.826 2.098 1.677 1.29 2.858 3.13 3.509 5.467l-2.04.569c-1.104-3.96-3.898-5.984-8.304-6.015-2.91.022-5.11.936-6.54 2.717C4.307 6.504 3.616 8.914 3.589 12c.027 3.086.718 5.496 2.057 7.164 1.43 1.781 3.631 2.695 6.54 2.717 2.623-.02 4.358-.631 5.8-2.045 1.647-1.613 1.618-3.593 1.09-4.798-.31-.71-.873-1.3-1.634-1.75-.192 1.352-.622 2.446-1.284 3.272-.886 1.102-2.14 1.704-3.73 1.79-1.202.065-2.361-.218-3.259-.801-1.063-.689-1.685-1.74-1.752-2.964-.065-1.19.408-2.285 1.33-3.082.88-.76 2.119-1.207 3.583-1.291a13.853 13.853 0 0 1 3.02.142c-.126-.742-.375-1.332-.75-1.757-.513-.586-1.308-.883-2.359-.89h-.029c-.844 0-1.992.232-2.721 1.32L7.734 7.847c.98-1.454 2.568-2.256 4.478-2.256h.044c3.194.02 5.097 1.975 5.287 5.388.108.046.216.094.321.142 1.49.7 2.58 1.761 3.154 3.07.797 1.82.871 4.79-1.548 7.158-1.85 1.81-4.094 2.628-7.277 2.65Zm1.003-11.69c-.242 0-.487.007-.739.021-1.836.103-2.98.946-2.916 2.143.067 1.256 1.452 1.839 2.784 1.767 1.224-.065 2.818-.543 3.086-3.71a10.5 10.5 0 0 0-2.215-.221Z"/></svg>'),
}

# ブランドマーク＝PixelRyu の竜アイコン（icon.webp）。
# ★2026-08-14 変更: それまでヘッダー/フッターには刷新時に作った「篆刻風の落款SVG」を
#   置いていたが、これは実在のロゴではなく私が意匠として起こしたもの。favicon /
#   apple-touch-icon / JSON-LD の Organization.logo / プレスキットの studio mark は
#   すべて icon.png（竜）なので、ブランドマークもそちらに統一する。
#   透過PNG/WebP なので明地・暗地どちらでも枠が出ない。
BRAND_ICON = "icon.webp?v=20260704170327"


def brandmark(rel: str, size: int = 30) -> str:
    return (f'<img class="pr-brandmark" src="{rel}{BRAND_ICON}" alt="" '
            f'width="{size}" height="{size}" decoding="async">')


# 旧・落款SVG（未使用。意匠の履歴として残す）
SEAL_SVG = (
    '<svg class="pr-seal-svg" viewBox="0 0 32 32" width="30" height="30" aria-hidden="true" focusable="false">'
    '<rect width="32" height="32" rx="3" fill="#C73E3A"/>'
    '<g stroke="#fff" stroke-width="2.4" fill="none" stroke-linecap="square">'
    '<path d="M9 8.5h14M16 8.5v4M11 13.5h10M11 18h10M11 22.5h10M21 13.5v9"/></g></svg>'
)
SEAL_SVG_SM = SEAL_SVG.replace('width="30" height="30"', 'width="22" height="22"')

GLOBE_SVG = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 2.5 15.4 0 18M12 3c-2.5 2.6-2.5 15.4 0 18"/></svg>'
)
BURGER_SVG = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path d="M4 7h16M4 12h16M4 17h16"/></svg>'
)
# テーマ切替のアイコン。「押すとどうなるか」を示す＝暗地では日、明地では月を出す。
SUN_SVG = (
    '<svg class="pr-ic-sun" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<circle cx="12" cy="12" r="4.2"/>'
    '<path d="M12 2.6v2.2M12 19.2v2.2M2.6 12h2.2M19.2 12h2.2'
    'M5.4 5.4l1.6 1.6M17 17l1.6 1.6M18.6 5.4L17 7M7 17l-1.6 1.6"/></svg>'
)
MOON_SVG = (
    '<svg class="pr-ic-moon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path d="M20 13.2A8.2 8.2 0 0 1 10.8 4a8.2 8.2 0 1 0 9.2 9.2z"/></svg>'
)

FO_START, FO_END = "<!-- pr-shell:follow start -->", "<!-- pr-shell:follow end -->"
H_START, H_END = "<!-- pr-shell:header start -->", "<!-- pr-shell:header end -->"
F_START, F_END = "<!-- pr-shell:footer start -->", "<!-- pr-shell:footer end -->"
C_START, C_END = "<!-- pr-shell:css start -->", "<!-- pr-shell:css end -->"
J_START, J_END = "<!-- pr-shell:js start -->", "<!-- pr-shell:js end -->"

NAV = [("games/", "Games", "nav_games"), ("about/", "About", "nav_about"),
       ("press/", "Press", "nav_press")]
NEWS_URL = "https://pixelryu.substack.com/"
# 地の色。assets/site.css の --bg-0（両テーマ）と一致させること。
# ページごとの <meta name="theme-color"> は旧アプリ配色のまま残っているので、
# 復元インラインで毎回上書きしてブラウザ UI の色を実際の地に合わせる。
DARK_BG, LIGHT_BG = "#0B0E13", "#F4F1EA"

EN = SHELL["en"]


def t(key: str) -> str:
    """英語の既定文言＋切替用の目印。site.js / gen_i18n_pages.py がこの属性で差し替える。"""
    return f'data-pr-i18n="{key}">{EN[key]}'


def a11y(key: str) -> str:
    """aria-label のように属性側を差し替えるもの。"""
    return f'aria-label="{EN[key]}" data-pr-i18n-attr="aria-label" data-pr-i18n="{key}"'


def theme_btn(with_text: bool) -> str:
    """ダーク/ライト切替ボタン。表示中のテーマと逆のアイコンだけを CSS で出す。

    可視ラベルがある側（バーガー内）には aria-label を付けない。aria-label は
    アクセシブル名を丸ごと上書きするので、見えている「テーマ」と読み上げ名が
    食い違い、音声操作で「テーマ」と言っても押せなくなる（WCAG 2.5.3）。"""
    if with_text:
        return (f'<button type="button" class="pr-theme" aria-pressed="false">'
                f'{SUN_SVG}{MOON_SVG}<span {t("nav_theme")}</span></button>')
    return (f'<button type="button" class="pr-theme" {a11y("aria_theme")} aria-pressed="false">'
            f'{SUN_SVG}{MOON_SVG}</button>')


def header_html(rel: str) -> str:
    nav = "".join(f'<a href="{rel}{h}" {t(k)}</a>' for h, _t, k in NAV)
    # リンク先も言語で変わる（日本語は note）。属性を訳す要素の中でも子は訳されるので、
    # ラベルは span に入れて text 側のキーを持たせる。
    nav_news = (f'<a href="{NEWS_URL}" target="_blank" rel="noopener" '
                f'data-pr-i18n-attr="href" data-pr-i18n="news_url">'
                f'<span {t("nav_news")}</span></a>')
    return (
        f'{H_START}\n'
        f'<a class="skip-link" href="#main" {t("skip")}</a>\n'
        f'<header class="pr-header">\n'
        f'  <div class="pr-header-in">\n'
        f'    <a class="pr-brand" href="{rel or "./"}" {a11y("aria_home")}>{brandmark(rel)}PixelRyu</a>\n'
        f'    <nav class="pr-nav" aria-label="Main">{nav}{nav_news}'
        f'<a class="pr-nav-lang" href="#pr-langs" {a11y("aria_lang")}>{GLOBE_SVG}</a>'
        f'{theme_btn(False)}</nav>\n'
        f'    <details class="pr-burger">\n'
        f'      <summary {a11y("aria_menu")}>{BURGER_SVG}</summary>\n'
        f'      <div class="pr-burger-menu">{nav}{nav_news}'
        f'<a href="#pr-langs" {t("nav_langs")}</a>{theme_btn(True)}</div>\n'
        f'    </details>\n'
        f'  </div>\n'
        f'</header>\n'
        f'{H_END}'
    )


def footer_html(rel: str, lang_base: str) -> str:
    """lang_base: 言語スイッチのリンク先の接頭辞（トップなら "", ゲームなら "<slug>/"）"""
    games = "".join(f'<li><a href="{rel}{s}/">{n}</a></li>' for s, n in GAMES)
    # data-pr-lang: クリック時に site.js が選択言語を localStorage へ保存する。
    # これが無いと、飛んだ先の言語ページで「保存済みの前の言語」が優先されて元に戻る。
    langs = "".join(
        f'<a href="{rel}{lang_base}{p}" hreflang="{c}" lang="{c}" data-pr-lang="{c}">{n}</a>'
        for c, n, p in LANGS
    )
    socials = "".join(
        f'<a href="{u}" target="_blank" rel="noopener" aria-label="{n}" title="{n}">{svg}</a>'
        for n, (u, svg) in SOCIAL_ICONS.items()
    )
    year = datetime.date.today().year
    return (
        f'{F_START}\n'
        f'<footer class="pr-footer">\n'
        f'  <div class="pr-footer-in">\n'
        f'    <div>\n'
        f'      <a class="pr-brand" href="{rel or "./"}">{brandmark(rel)}PixelRyu</a>\n'
        f'      <p style="font-size:14px;margin:14px 0 16px;max-width:30ch" '
        f'{t("blurb")}</p>\n'
        f'      <div class="pr-news">\n'
        f'        <p {t("news_p")}</p>\n'
        f'        <a class="pr-btn pr-btn-primary" href="{NEWS_URL}" target="_blank" rel="noopener" '
        f'style="font-size:14px;padding:9px 16px" data-pr-i18n-attr="href" data-pr-i18n="news_url">'
        f'<span {t("news_cta")}</span></a>\n'
        f'      </div>\n'
        f'    </div>\n'
        f'    <div>\n'
        f'      <h4 {t("h_explore")}</h4>\n'
        f'      <ul>\n'
        f'        <li><a href="{rel}games/" {t("e_games")}</a></li>\n'
        f'        <li><a href="{rel}roblox/" {t("e_roblox")}</a></li>\n'
        f'        <li><a href="{rel}about/" {t("e_about")}</a></li>\n'
        f'        <li><a href="{rel}press/" {t("e_press")}</a></li>\n'
        f'        <li><a href="{rel}support/" {t("e_support")}</a></li>\n'
        f'      </ul>\n'
        f'    </div>\n'
        f'    <div>\n'
        f'      <h4 {t("h_games")}</h4>\n'
        f'      <ul style="columns:2;column-gap:18px">{games}</ul>\n'
        f'    </div>\n'
        f'    <div>\n'
        f'      <h4 id="pr-langs" {t("h_langs")}</h4>\n'
        f'      <div class="pr-footer-langs">{langs}</div>\n'
        f'      <h4 style="margin-top:20px" {t("h_follow")}</h4>\n'
        f'      <div class="social pr-footer-social">{socials}</div>\n'
        f'    </div>\n'
        f'  </div>\n'
        f'  <div class="pr-footer-bottom">\n'
        f'    <span>© {year} PixelRyu</span>\n'
        f'    {brandmark(rel, 22)}\n'
        f'    <span><a href="{rel}support/" {t("contact")}</a> · '
        f'<a href="mailto:idev10752@gmail.com">idev10752@gmail.com</a></span>\n'
        f'  </div>\n'
        f'</footer>\n'
        f'{F_END}'
    )


def follow_html() -> str:
    """本文用の Follow 節（SNS 8アイコン）。ゲームページが元から持っているものと同型。"""
    icons = "".join(
        f'\n      <a href="{u}" target="_blank" rel="noopener" aria-label="{n}" title="{n}">{svg}</a>'
        for n, (u, svg) in SOCIAL_ICONS.items()
    )
    return (f'{FO_START}\n'
            f'  <h2 class="social-heading" {t("h_follow")}</h2>\n'
            f'  <div class="social">{icons}\n  </div>\n'
            f'{FO_END}')


def ensure_follow(html: str) -> str:
    """本文（フッターより前）に Follow 節が無いページにだけ追加する。
    ゲームページは元から `.social` を持つので二重にならない。冪等。

    ★挿入位置は毎回計算し直す（マーカーがあっても中身だけ差し替えない）。
      以前は「マーカーがあれば中身を置換」だけだったため、一度おかしな場所に
      入ると永久にそこへ居座った。実際トップでは `<div id="lang-overlay">` の
      閉じタグを container の閉じと誤認し、Follow 節が display:none の
      オーバーレイの中に入って全ページで見えなくなっていた。"""
    if FO_START in html:
        pat = re.compile(re.escape(FO_START) + r".*?" + re.escape(FO_END) + r"\n?", re.S)
        html = pat.sub("", html, count=1)     # 一度はがしてから置き直す
    idx = html.find(F_START)
    body = html[:idx] if idx > 0 else html
    if re.search(r'<div class="social[^"]*"', body):
        return html          # 本文に既にある（ゲームページ）
    if idx <= 0:
        return html
    # container の閉じタグを探す。ただし本文より後ろにある装飾要素
    # （#lang-overlay など）の閉じタグを拾わないよう、探索上限を手前で切る。
    limit = idx
    ov = html.find('<div id="lang-overlay"')
    if 0 < ov < limit:
        limit = ov
    close = html.rfind("</div>", 0, limit)
    if close < 0:
        return html
    return html[:close] + follow_html() + "\n" + html[close:]


def block(start: str, end: str, body: str) -> str:
    return body


def replace_or_insert(html: str, start: str, end: str, payload: str, anchor: str,
                      where: str = "after") -> str:
    """マーカー間を置換。無ければ anchor の前後に挿入する（冪等）。"""
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if pat.search(html):
        return pat.sub(lambda _m: payload, html, count=1)
    if anchor not in html:
        raise SystemExit(f"アンカーが見つからない: {anchor!r}")
    if where == "after":
        return html.replace(anchor, anchor + "\n" + payload, 1)
    return html.replace(anchor, payload + "\n" + anchor, 1)


def body_open_tag(html: str) -> str:
    m = re.search(r"<body[^>]*>", html)
    if not m:
        raise SystemExit("<body> が無い")
    return m.group(0)


STYLE_REMOVED = "<!-- pr-shell: inline style removed → assets/site.css -->"


def set_body_class(html: str, cls: str) -> str:
    """<body> に識別クラスを付ける（冪等）。"""
    m = re.search(r"<body([^>]*)>", html)
    if not m:
        raise SystemExit("<body> が無い")
    attrs = m.group(1)
    if cls in attrs:
        return html
    if 'class="' in attrs:
        new = re.sub(r'class="([^"]*)"', lambda mm: f'class="{mm.group(1)} {cls}"', attrs, count=1)
    else:
        new = attrs + f' class="{cls}"'
    return html[: m.start()] + f"<body{new}>" + html[m.end():]


def strip_inline_style(html: str) -> str:
    """head 内のアプリ固有インライン <style> を撤去する（冪等）。
    見た目は assets/site.css に一本化される。撤去済みならマーカーがあるので何もしない。"""
    if STYLE_REMOVED in html:
        return html
    m = re.search(r"[ \t]*<style>.*?</style>\n?", html, re.S)
    if not m:
        return html
    return html[: m.start()] + STYLE_REMOVED + "\n" + html[m.end():]


def apply_to(path: str, rel: str, lang_base: str, ver: str, is_home: bool,
             strip_style: bool = False, body_cls: str = "") -> bool:
    with open(path, encoding="utf-8") as f:
        orig = f.read()
    html = orig

    # 0) body クラス / インライン style の撤去
    if body_cls:
        html = set_body_class(html, body_cls)
    if strip_style:
        html = strip_inline_style(html)

    # 1) site.css を </head> 直前へ。
    #    テーマの復元だけは **同期インライン** で先に走らせる（外部 JS だと
    #    一瞬ダークが描画されてから明地に変わる＝チラつきが必ず出るため）。
    css = (f'{C_START}\n'
           f'<link rel="stylesheet" href="{rel}assets/site.css?v={ver}">\n'
           f'<script>(function(){{try{{var t=localStorage.getItem("pixelryu_theme");'
           f'if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t);'
           f'var m=document.querySelector(\'meta[name="theme-color"]\');'
           f'if(m)m.setAttribute("content",t==="light"?"{LIGHT_BG}":"{DARK_BG}");}}'
           f'catch(e){{}}}})();</script>\n{C_END}')
    html = replace_or_insert(html, C_START, C_END, css, "</head>", where="before")

    # 2) ヘッダーを <body> 直後へ
    html = replace_or_insert(html, H_START, H_END, header_html(rel), body_open_tag(html), where="after")

    # 3) フッター + site.js を </body> 直前へ
    foot = footer_html(rel, lang_base)
    # defer は記述順に実行されるので、辞書 → site.js の順で確実に読める。
    js = (f'{J_START}\n'
          f'<script src="{rel}assets/shell-i18n.js?v={ver}" defer></script>\n'
          f'<script src="{rel}assets/site.js?v={ver}" defer></script>\n{J_END}')
    html = replace_or_insert(html, F_START, F_END, foot, "</body>", where="before")
    html = replace_or_insert(html, J_START, J_END, js, "</body>", where="before")

    # 3.5) 本文に Follow 節が無いページ（トップ・新設セクション）へ追加。
    #      ★必ずフッター挿入の **後** に呼ぶこと。ensure_follow は挿入位置の基準に
    #        フッターのマーカーを使うので、先に呼ぶと gen_pages.py で作り直した直後の
    #        ページ（マーカーがまだ無い）では黙って何もせず、Follow 節が2回目の実行まで
    #        入らない。実際 /games/ /roblox/ /support/ /about/ /press/ が本番でそうなっていた。
    html = ensure_follow(html)

    # 4) ランドマーク（skip-link の着地点）
    if is_home:
        if '<main id="main">' not in html:
            html = html.replace("<main>", '<main id="main">', 1)
    else:
        if 'class="container" id="main"' not in html:
            html = html.replace(
                '<div class="container">',
                '<div class="container" id="main" role="main">', 1)

    if html != orig:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        return True
    return False


def targets():
    out = []
    for name in sorted(os.listdir(BASE)):
        p = os.path.join(BASE, name)
        if not os.path.isdir(p) or name in LANG_DIRS or name.startswith(".") or name == "tools":
            continue
        if os.path.exists(os.path.join(p, "index.html")):
            out.append(name)
    return out


def write_shell_i18n_js() -> str:
    """assets/shell-i18n.js を shell_i18n.py から生成する（手で編集しない生成物）。"""
    body = json.dumps(SHELL, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    out = ("/* 生成物 — 編集しないこと。正本 = tools/shell_i18n.py\n"
           "   共通シェル（ヘッダー/フッター/Follow）の12言語辞書。site.js が適用する。 */\n"
           "window.PR_SHELL_I18N=%s;\n" % body)
    path = os.path.join(BASE, "assets", "shell-i18n.js")
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old != out:
        with open(path, "w", encoding="utf-8") as f:
            f.write(out)
        return "assets/shell-i18n.js"
    return ""


def main():
    shell_i18n_check()
    ver = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    only = sys.argv[1:]
    changed = []
    gen = write_shell_i18n_js()
    if gen:
        changed.append(gen)

    # 新設ページ（ゲームではないので lang_base は自分自身、style も持たない）
    new_pages = {"games", "roblox", "support", "about", "press"}

    # トップ
    if not only or "" in only or "home" in only:
        if apply_to(os.path.join(BASE, "index.html"), "", "", ver,
                    is_home=True, body_cls="pr-home"):
            changed.append("index.html")

    for slug in targets():
        if only and "home" not in only and slug not in only:
            continue
        path = os.path.join(BASE, slug, "index.html")
        is_new = slug in new_pages
        lang_base = (slug + "/") if slug in MIRRORED else ""
        if apply_to(path, "../", lang_base, ver, is_home=False,
                    strip_style=not is_new,
                    body_cls="pr-page" if is_new else "pr-game"):
            changed.append(f"{slug}/index.html")

    print(f"?v={ver}")
    print(f"更新 {len(changed)} ファイル")
    for c in changed:
        print("  ", c)


if __name__ == "__main__":
    main()
