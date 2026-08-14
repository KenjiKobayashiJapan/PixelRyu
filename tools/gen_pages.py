#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_pages.py — 新設ページ（/games/ /roblox/ /support/ /about/ /press/）を生成する。

設計:
  * ゲームのデータ（名前・ジャンル・アイコン・ストアリンク・説明の i18n キー）は
    トップの index.html から実データを抽出する。二重管理をしない＝新作追加時に
    トップを直せばここも自動で追従する。
  * 12言語ページは tools/gen_i18n_pages.py が作る。ここが出すのは英語の正本のみ。
    そのため gen_i18n_pages.py の要件を厳守する:
      - i18n に12言語すべてのキーがある
      - <title data-i18n="title"> と meta description の data-i18n 形
      - canonical / og:url / og:locale が既存ページと同じ1属性形
      - スイッチャは detectLang / setLang のテンプレB形（アンカー行がバイト一致）
  * /press/ は英語のみ（メディア向け）。gen_i18n_pages.py の対象に入れない。

使い方: python3 tools/gen_pages.py
"""
import os
import re
import json
import html as html_mod
import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://pixelryu.github.io/"
TS = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
# 新設ページの12言語文言。リポジトリ内に置く（以前は一時ディレクトリを指していて、
# そこが消えるとこのジェネレータが動かなくなる状態だった）。
I18N_PAGES_JSON = os.environ.get(
    "PAGES_I18N", os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages_i18n.json"))
LANGS = ["en", "ja", "zh", "ko", "hi", "id", "de", "fr", "it", "es", "pt", "ru"]
LANG_NAMES = {
    "en": "English", "ja": "日本語", "zh": "中文", "ko": "한국어", "hi": "हिन्दी",
    "id": "Indonesia", "de": "Deutsch", "fr": "Français", "it": "Italiano",
    "es": "Español", "pt": "Português", "ru": "Русский",
}
OG_LOCALE = {
    "en": "en_US", "ja": "ja_JP", "zh": "zh_CN", "ko": "ko_KR", "hi": "hi_IN",
    "id": "id_ID", "de": "de_DE", "fr": "fr_FR", "it": "it_IT", "es": "es_ES",
    "pt": "pt_BR", "ru": "ru_RU",
}
GA = """<link rel="preconnect" href="https://www.googletagmanager.com" crossorigin>
<link rel="dns-prefetch" href="https://www.google-analytics.com">
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-M5MH53Z8LM"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('consent', 'default', {
    'ad_storage': 'denied',
    'ad_user_data': 'denied',
    'ad_personalization': 'denied',
    'analytics_storage': 'denied'
  });
  gtag('js', new Date());
  gtag('config', 'G-M5MH53Z8LM');
</script>"""


# ---------------------------------------------------------------- 抽出
def extract_games():
    """トップの index.html からカード情報を抜く（＝作品カタログの正本はトップ）。

    ★件数が 18 で、gen_i18n_pages.py / gen_sitemap.py の GAMES(19) と一致しないのは
    意図どおり。19 は「ページ数」、18 は「作品数」で、差の 1 は liquid-glow（旧ページ）。
    旧 liquid-glow は liquid-glow-cosmic と同一作品の旧版ページで、canonical は cosmic を
    指しトップのカードにも載せていない。よって一覧・年表・フッターにも出さず、
    /about/ の「18 games」も作品数として正しい。旧ページ自体は既存 URL 保全のため
    sitemap には残す（この方針を変えるならトップのカードを足すのが起点）。
    """
    src = open(os.path.join(BASE, "index.html"), encoding="utf-8").read()
    lines = src.split("\n")
    starts = [i for i, l in enumerate(lines) if '<li class="game-card"' in l]
    ends = []
    for s in starts:
        depth = 0
        for i in range(s, len(lines)):
            depth += lines[i].count("<li ") + lines[i].count("<li>")
            depth -= lines[i].count("</li>")
            if depth == 0:
                ends.append(i)
                break
    games = []
    for s, e in zip(starts, ends):
        seg = "\n".join(lines[s:e + 1])
        slug = re.search(r'href="([a-z0-9\-]+)/"', seg).group(1)
        # liquid-glow-cosmic だけタイトルが i18n 化されていない（固定文字列）
        tm = re.search(r'data-i18n="([a-z0-9_]+_title)"', seg)
        if tm:
            title_key = tm.group(1)
            title_en = re.search(r'data-i18n="' + title_key + r'">([^<]*)<', seg).group(1)
        else:
            title_key = None
            title_en = re.search(r'href="' + re.escape(slug) + r'/"[^>]*>([^<]*)<', seg).group(1)
        # 抽出元は既にエスケープ済み HTML。このあと html.escape() を通すので、
        # ここで実体参照を戻しておかないと "&amp;" が "&amp;amp;" に二重化する。
        title_en = html_mod.unescape(title_en)
        desc_key = re.search(r'class="desc" data-i18n="([a-z0-9_]+)"', seg).group(1)
        icon = re.search(r'class="game-icon"[^>]*src="([^"]+)"', seg)
        if not icon:
            icon = re.search(r'src="([^"]*icon[^"]*)"', seg)
        no = re.search(r'class="game-no">(\d+)<', seg)
        genres = sorted(set(re.findall(r'genre-tag genre-([a-z]+)', seg)))
        ios = re.search(r'href="(https://apps\.apple\.com/[^"]+)"', seg)
        rbx = re.search(r'href="(https://www\.roblox\.com/games/[^"]+)"', seg)
        badges = re.search(r'<div class="store-badges[^"]*"[^>]*>(.*?)</div>', seg, re.S)
        games.append({
            "slug": slug, "title_key": title_key, "title_en": title_en,
            "desc_key": desc_key, "icon": icon.group(1) if icon else f"{slug}/icon.webp",
            "no": no.group(1) if no else "", "genres": genres,
            "ios": ios.group(1) if ios else None,
            "roblox": rbx.group(1) if rbx else None,
            "badges": badges.group(1).strip() if badges else "",
        })
    return games


def extract_home_i18n():
    """トップの i18n から、ゲーム名・説明・ジャンル語だけを取り出す。"""
    src = open(os.path.join(BASE, "index.html"), encoding="utf-8").read()
    i = src.find("const i18n = {")
    depth, j, end = 0, src.find("{", i), None
    while j < len(src):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                end = j
                break
        j += 1
    block = src[src.find("{", i):end + 1]
    # JS リテラル（キー非引用）を JSON へ寄せる
    txt = re.sub(r'(?m)^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', block)
    txt = re.sub(r",(\s*[}\]])", r"\1", txt)
    return json.loads(txt)


# ---------------------------------------------------------------- 組み立て
def head(slug, i18n_all, title_key, desc_key, extra_ld=""):
    en = i18n_all["en"]
    title = html_mod.escape(en[title_key])
    desc = html_mod.escape(en[desc_key])
    alts = "\n".join(
        f'<link rel="alternate" hreflang="{L}" href="{SITE}{slug}/{"" if L == "en" else L + "/"}">'
        for L in LANGS
    )
    oglocs = "\n".join(
        f'<meta property="og:locale:alternate" content="{OG_LOCALE[L]}">' for L in LANGS if L != "en"
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{GA}
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title data-i18n="title">{title}</title>
<meta name="description" data-i18n-attr="content" data-i18n="meta_desc" content="{desc}">
<!-- SEO/LLMO start (managed) -->
<link rel="canonical" href="{SITE}{slug}/">
{alts}
<link rel="alternate" hreflang="x-default" href="{SITE}{slug}/">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<meta name="author" content="PixelRyu">
<meta name="publisher" content="PixelRyu">
<meta name="theme-color" content="#0B0E13">
<link rel="icon" type="image/png" href="{SITE}favicon.png">
<link rel="apple-touch-icon" href="{SITE}apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="PixelRyu">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{SITE}{slug}/">
<meta property="og:image" content="{SITE}og.png?v=20260606192649">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="PixelRyu — small games crafted in Japan">
<meta property="og:locale" content="en_US">
{oglocs}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{SITE}og.png?v=20260606192649">
{extra_ld}
<!-- SEO/LLMO end -->
</head>
<body>
<div class="container">
  <div class="lang-switch">
    <select id="lang-select" aria-label="Language"></select>
  </div>"""


def i18n_script(i18n_all):
    langs_js = ",\n    ".join(
        "{ code: '%s', label: '%s' }" % (L, LANG_NAMES[L]) for L in LANGS
    )
    dict_js = ",\n".join(
        f'    "{L}": ' + json.dumps(i18n_all[L], ensure_ascii=False) for L in LANGS
    )
    return """<script>
  const LANGUAGES = [
    %s
  ];
  const i18n = {
%s
  };
  const LANG_STORAGE_KEY = 'pixelryu_lang_v2';
  function detectLang() {
    try { const stored = localStorage.getItem(LANG_STORAGE_KEY); if (stored && i18n[stored]) return stored; } catch (e) {}
    const raw = (navigator.language || 'en').toLowerCase();
    for (const l of LANGUAGES) if (raw === l.code) return l.code;
    const head = raw.split(/[-_]/)[0];
    for (const l of LANGUAGES) if (head === l.code) return l.code;
    return 'en';
  }
  function setLang(lang, persist) {
    const dict = i18n[lang]; if (!dict) return;
    if (persist) { try { localStorage.setItem(LANG_STORAGE_KEY, lang); } catch (e) {} }
    document.documentElement.lang = lang;
    document.querySelectorAll('[data-i18n]').forEach(function(el) {
      const key = el.getAttribute('data-i18n');
      if (key in dict) el.textContent = dict[key];
    });
    document.querySelectorAll('[data-i18n-attr]').forEach(function(el) {
      const key = el.getAttribute('data-i18n');
      const attr = el.getAttribute('data-i18n-attr');
      if (key in dict) el.setAttribute(attr, dict[key]);
    });
    const sel = document.getElementById('lang-select');
    if (sel) sel.value = lang;
  }
  (function init() {
    const sel = document.getElementById('lang-select');
    for (const l of LANGUAGES) {
      const opt = document.createElement('option');
      opt.value = l.code; opt.textContent = l.label;
      sel && sel.appendChild(opt);
    }
    setLang(detectLang(), false);
    if (sel) sel.addEventListener('change', function() { setLang(sel.value, true); });
  })();
</script>""" % (langs_js, dict_js)


def tail(i18n_all):
    return f"""</div>
{i18n_script(i18n_all)}
<script src="../breadcrumb.js?v={TS}" defer></script>
</body>
</html>
"""


def rebase(markup: str) -> str:
    """トップから借りたマークアップの相対パスを1階層深いページ用に直す。
    トップの `href="kado/#tester-heading"` は /games/ から見ると /games/kado/… になり
    404 する（言語ミラーでは絶対URLに焼き込まれるのでさらに悪化する）。"""
    markup = re.sub(r'href="(?!https?:|#|mailto:|\.\./)([^"]+)"', r'href="../\1"', markup)
    markup = re.sub(r'src="(?!https?:|data:|\.\./)([^"]+)"', r'src="../\1"', markup)
    return markup


def filter_bar():
    """ジャンル絞り込みのチップ列。トップの同名ブロックからそのまま借りる（重複管理しない）。"""
    src = open(os.path.join(BASE, "index.html"), encoding="utf-8").read()
    m = re.search(r'<div class="genre-filter".*?</div>\n', src, re.S)
    if not m:
        raise SystemExit("gen_pages: トップに .genre-filter が無い（構造が変わった）")
    return "  " + m.group(0).strip()


def feed_script():
    """一覧の制御スクリプト（絞り込み＋無限スクロール）。正本はトップの1本だけ。
    マーカーで囲まれた実体をそのまま持ってくるので、片方だけ直して食い違うことがない。"""
    src = open(os.path.join(BASE, "index.html"), encoding="utf-8").read()
    m = re.search(r'<!-- pr-feed:script start -->\n(.*?)\n<!-- pr-feed:script end -->', src, re.S)
    if not m:
        raise SystemExit("gen_pages: トップに pr-feed:script マーカーが無い")
    return m.group(1)


def card_html(g, mode="full", home=None):
    """一覧カード。mode=roblox なら Roblox バッジのみ。

    ★desc は英語の実文を必ず入れる。空タグにして実行時の setLang に任せると、
      JS を実行しないクローラ（AI 系）には説明が1文字も見えない。しかも言語ミラーは
      gen_i18n_pages が静的に焼き込むので、英語の正規ページだけ中身が無い、という
      逆転が起きる。home はトップの i18n（extract_home_i18n() の戻り）。"""
    badges = rebase(g["badges"])
    if mode == "roblox":
        m = re.search(r'<a class="roblox-badge".*?</a>', badges, re.S)
        badges = m.group(0) if m else ""
    genres = "".join(
        f'<span class="genre-tag genre-{gr}"><span data-i18n="genre_{gr}">{gr.title()}</span></span>'
        for gr in g["genres"]
    )
    return f"""      <li class="game-card" data-game="{g['slug']}">
        <div class="game-head">
          <img class="game-icon" width="56" height="56" loading="lazy" src="../{g['icon']}" alt="">
          <div class="game-title">
            <span class="game-name-row"><span class="game-no">{g['no']}</span><a href="../{g['slug']}/"{f' data-i18n="{g["title_key"]}"' if g['title_key'] else ''}>{html_mod.escape(g['title_en'])}</a></span>
            <span class="genre-tags">{genres}</span>
          </div>
        </div>
        <div class="desc" data-i18n="{g['desc_key']}">{html_mod.escape((home or {}).get('en', {}).get(g['desc_key'], ''))}</div>
        <div class="store-badges">{badges}</div>
      </li>"""


# ---------------------------------------------------------------- 各ページ
def page_games(games, T, home):
    i18n_all = {}
    for L in LANGS:
        d = {"title": T[L]["games_title"], "meta_desc": T[L]["games_meta"],
             "h1": T[L]["games_h1"], "lead": T[L]["games_lead"]}
        for g in games:
            for k in (g["title_key"], g["desc_key"]):
                if k in home[L]:
                    d[k] = home[L][k]
        for k in ("genre_puzzle", "genre_action", "filter_all"):   # 絞り込みチップの文言
            if k in home[L]:
                d[k] = home[L][k]
        i18n_all[L] = d

    items = "".join(
        f'{{"@type":"ListItem","position":{i+1},"name":{json.dumps(g["title_en"].split(" — ")[0], ensure_ascii=False)},'
        f'"url":"{SITE}{g["slug"]}/"}}' + ("," if i < len(games) - 1 else "")
        for i, g in enumerate(games)
    )
    ld = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"CollectionPage",'
          f'"name":{json.dumps(T["en"]["games_title"], ensure_ascii=False)},"url":"{SITE}games/",'
          f'"description":{json.dumps(T["en"]["games_meta"], ensure_ascii=False)},'
          '"isPartOf":{"@type":"WebSite","name":"PixelRyu","url":"' + SITE + '"},'
          '"mainEntity":{"@type":"ItemList","name":"Games by PixelRyu",'
          '"itemListOrder":"https://schema.org/ItemListOrderDescending",'
          f'"numberOfItems":{len(games)},"itemListElement":[{items}]}}}}</script>\n'
          '<script type="application/ld+json">{"@context":"https://schema.org","@type":"BreadcrumbList",'
          '"itemListElement":[{"@type":"ListItem","position":1,"name":"PixelRyu","item":"' + SITE + '"},'
          '{"@type":"ListItem","position":2,"name":"Games","item":"' + SITE + 'games/"}]}</script>')

    # ジャンル別に節を分けるのはやめ、トップと同じ「1本の一覧＋ジャンル絞り込み＋無限スクロール」に
    # 揃えた。2節構成だと bounce-cat のように2ジャンル持つ作品が二重に並び、作品数も合わなくなる。
    body = f"""
  <h1 data-i18n="h1">{html_mod.escape(T['en']['games_h1'])}</h1>
  <p class="pr-lead" data-i18n="lead">{html_mod.escape(T['en']['games_lead'])}</p>

{filter_bar()}
  <ul class="game-list">
{chr(10).join(card_html(g, home=home) for g in games)}
  </ul>
  <div id="list-loader" aria-hidden="true"><span class="pr-spinner"></span></div>
  <div id="scroll-sentinel" aria-hidden="true"></div>
{feed_script()}
"""
    return head("games", i18n_all, "title", "meta_desc", ld) + body + tail(i18n_all)


def page_roblox(games, T, home):
    live = [g for g in games if g["roblox"]]
    i18n_all = {}
    for L in LANGS:
        d = {"title": T[L]["roblox_title"], "meta_desc": T[L]["roblox_meta"],
             "h1": T[L]["roblox_h1"], "lead": T[L]["roblox_lead"], "note": T[L]["roblox_note"]}
        for g in live:
            for k in (g["title_key"], g["desc_key"]):
                if k in home[L]:
                    d[k] = home[L][k]
        for gr in ("puzzle", "action"):
            if f"genre_{gr}" in home[L]:
                d[f"genre_{gr}"] = home[L][f"genre_{gr}"]
        i18n_all[L] = d

    items = "".join(
        f'{{"@type":"ListItem","position":{i+1},"name":{json.dumps(g["title_en"].split(" — ")[0], ensure_ascii=False)},'
        f'"url":{json.dumps(g["roblox"], ensure_ascii=False)}}}' + ("," if i < len(live) - 1 else "")
        for i, g in enumerate(live)
    )
    ld = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"CollectionPage",'
          f'"name":{json.dumps(T["en"]["roblox_title"], ensure_ascii=False)},"url":"{SITE}roblox/",'
          f'"description":{json.dumps(T["en"]["roblox_meta"], ensure_ascii=False)},'
          '"isPartOf":{"@type":"WebSite","name":"PixelRyu","url":"' + SITE + '"},'
          f'"mainEntity":{{"@type":"ItemList","name":"PixelRyu games on Roblox","numberOfItems":{len(live)},'
          f'"itemListElement":[{items}]}}}}</script>\n'
          '<script type="application/ld+json">{"@context":"https://schema.org","@type":"BreadcrumbList",'
          '"itemListElement":[{"@type":"ListItem","position":1,"name":"PixelRyu","item":"' + SITE + '"},'
          '{"@type":"ListItem","position":2,"name":"Roblox","item":"' + SITE + 'roblox/"}]}</script>')

    body = f"""
  <h1 data-i18n="h1">{html_mod.escape(T['en']['roblox_h1'])}</h1>
  <p class="pr-lead" data-i18n="lead">{html_mod.escape(T['en']['roblox_lead'])}</p>
  <p class="pr-lead" data-i18n="note">{html_mod.escape(T['en']['roblox_note'])}</p>
  <p><a class="pr-btn pr-btn-ghost" href="https://www.roblox.com/users/8721546043/profile" target="_blank" rel="noopener">PixelRyu_Japan on Roblox</a></p>
  <ul class="game-list">
{chr(10).join(card_html(g, mode='roblox', home=home) for g in live)}
  </ul>
"""
    return head("roblox", i18n_all, "title", "meta_desc", ld) + body + tail(i18n_all)


def page_support(T):
    i18n_all = {}
    for L in LANGS:
        d = {"title": T[L]["support_title"], "meta_desc": T[L]["support_meta"],
             "h1": T[L]["support_h1"], "lead": T[L]["support_lead"],
             "contact_h": T[L]["support_contact_h"], "contact_body": T[L]["support_contact_body"],
             "faq_h": T[L]["support_faq_h"]}
        for n in range(1, 7):
            d[f"q{n}"] = T[L][f"support_q{n}"]
            d[f"a{n}"] = T[L][f"support_a{n}"]
        i18n_all[L] = d

    faq_items = "".join(
        '{"@type":"Question","name":' + json.dumps(T["en"][f"support_q{n}"], ensure_ascii=False) +
        ',"acceptedAnswer":{"@type":"Answer","text":' + json.dumps(T["en"][f"support_a{n}"], ensure_ascii=False) + "}}" +
        ("," if n < 6 else "")
        for n in range(1, 7)
    )
    ld = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"ContactPage",'
          f'"name":{json.dumps(T["en"]["support_title"], ensure_ascii=False)},"url":"{SITE}support/",'
          '"mainEntity":{"@type":"Organization","name":"PixelRyu","url":"' + SITE + '",'
          '"contactPoint":{"@type":"ContactPoint","email":"idev10752@gmail.com","contactType":"customer support"}}}</script>\n'
          '<script type="application/ld+json">{"@context":"https://schema.org","@type":"FAQPage","mainEntity":['
          + faq_items + ']}</script>\n'
          '<script type="application/ld+json">{"@context":"https://schema.org","@type":"BreadcrumbList",'
          '"itemListElement":[{"@type":"ListItem","position":1,"name":"PixelRyu","item":"' + SITE + '"},'
          '{"@type":"ListItem","position":2,"name":"Support","item":"' + SITE + 'support/"}]}</script>')

    faq = "\n".join(
        f"""    <details>
      <summary data-i18n="q{n}">{html_mod.escape(T['en'][f'support_q{n}'])}</summary>
      <p class="pr-faq-a" data-i18n="a{n}">{html_mod.escape(T['en'][f'support_a{n}'])}</p>
    </details>""" for n in range(1, 7)
    )
    body = f"""
  <h1 data-i18n="h1">{html_mod.escape(T['en']['support_h1'])}</h1>
  <p class="pr-lead" data-i18n="lead">{html_mod.escape(T['en']['support_lead'])}</p>

  <h2 data-i18n="contact_h">{html_mod.escape(T['en']['support_contact_h'])}</h2>
  <div class="tester-card">
    <p data-i18n="contact_body">{html_mod.escape(T['en']['support_contact_body'])}</p>
    <p><a class="pr-btn pr-btn-primary" href="mailto:idev10752@gmail.com">idev10752@gmail.com</a></p>
  </div>

  <h2 data-i18n="faq_h">{html_mod.escape(T['en']['support_faq_h'])}</h2>
  <div class="pr-faq">
{faq}
  </div>
"""
    return head("support", i18n_all, "title", "meta_desc", ld) + body + tail(i18n_all)


def page_about(games, T):
    i18n_all = {}
    for L in LANGS:
        i18n_all[L] = {
            "title": T[L]["about_title"], "meta_desc": T[L]["about_meta"],
            "h1": T[L]["about_h1"], "lead": T[L]["about_lead"],
            "story_h": T[L]["about_story_h"], "story_1": T[L]["about_story_1"],
            "story_2": T[L]["about_story_2"], "story_3": T[L]["about_story_3"],
            "timeline_h": T[L]["about_timeline_h"], "stats_h": T[L]["about_stats_h"],
            "contact_h": T[L]["about_contact_h"], "contact_body": T[L]["about_contact_body"],
            "devlog_h": T[L]["about_devlog_h"], "devlog_body": T[L]["about_devlog_body"],
            "stat_games": T[L].get("stat_games", "games"),
            "stat_langs": T[L].get("stat_langs", "languages"),
            "stat_platforms": T[L].get("stat_platforms", "platforms"),
        }
    ld = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"AboutPage",'
          f'"name":{json.dumps(T["en"]["about_title"], ensure_ascii=False)},"url":"{SITE}about/",'
          '"mainEntity":{"@type":"Person","name":"Ryu","alternateName":"PixelRyu",'
          '"jobTitle":"Independent game developer","url":"' + SITE + 'about/",'
          '"worksFor":{"@type":"Organization","name":"PixelRyu","url":"' + SITE + '"},'
          '"sameAs":["https://pixelryu.substack.com/","https://note.com/pixelryu",'
          '"https://www.youtube.com/@PixelRyu-Japan","https://x.com/PixelRyu10752",'
          '"https://www.instagram.com/pixelryu/","https://www.threads.com/@pixelryu"]}}</script>\n'
          '<script type="application/ld+json">{"@context":"https://schema.org","@type":"BreadcrumbList",'
          '"itemListElement":[{"@type":"ListItem","position":1,"name":"PixelRyu","item":"' + SITE + '"},'
          '{"@type":"ListItem","position":2,"name":"About","item":"' + SITE + 'about/"}]}</script>')

    tl = "".join(
        f'<li><a href="../{g["slug"]}/" title="{html_mod.escape(g["title_en"])}">'
        f'<img src="../{g["icon"]}" alt="{html_mod.escape(g["title_en"].split(" — ")[0])}" '
        f'width="56" height="56" loading="lazy"><span>{g["no"]}</span></a></li>'
        for g in sorted(games, key=lambda x: x["no"])
    )
    ios_n = sum(1 for g in games if g["ios"])
    rbx_n = sum(1 for g in games if g["roblox"])
    body = f"""
  <div class="pr-profile">
    <img class="pr-mascot" src="../icon.webp?v=20260704170327" alt="PixelRyu"
         width="384" height="384" fetchpriority="high" decoding="async">
    <div>
      <h1 data-i18n="h1">{html_mod.escape(T['en']['about_h1'])}</h1>
      <p class="pr-lead" data-i18n="lead">{html_mod.escape(T['en']['about_lead'])}</p>
    </div>
  </div>

  <div class="pr-washi">
    <div class="pr-stats">
      <div class="pr-stat"><b>{len(games)}</b><span data-i18n="stat_games">games</span></div>
      <div class="pr-stat"><b>12</b><span data-i18n="stat_langs">languages</span></div>
      <div class="pr-stat"><b>3</b><span data-i18n="stat_platforms">platforms</span></div>
    </div>
  </div>

  <h2 data-i18n="timeline_h">{html_mod.escape(T['en']['about_timeline_h'])}</h2>
  <ul class="pr-timeline">{tl}</ul>
  <p style="font-size:13.5px;color:var(--text-2)">{len(games)} released · {ios_n} on the App Store · {rbx_n} on Roblox</p>

  <h2 data-i18n="story_h">{html_mod.escape(T['en']['about_story_h'])}</h2>
  <div class="tester-card">
    <p data-i18n="story_1">{html_mod.escape(T['en']['about_story_1'])}</p>
    <p data-i18n="story_2">{html_mod.escape(T['en']['about_story_2'])}</p>
    <p data-i18n="story_3">{html_mod.escape(T['en']['about_story_3'])}</p>
  </div>

  <h2 data-i18n="devlog_h">{html_mod.escape(T['en']['about_devlog_h'])}</h2>
  <p data-i18n="devlog_body">{html_mod.escape(T['en']['about_devlog_body'])}</p>
  <p>
    <a class="pr-btn pr-btn-ghost" href="https://pixelryu.substack.com/" target="_blank" rel="noopener">Substack (English)</a>
    <a class="pr-btn pr-btn-ghost" href="https://note.com/pixelryu" target="_blank" rel="noopener">note (日本語)</a>
  </p>

  <h2 data-i18n="contact_h">{html_mod.escape(T['en']['about_contact_h'])}</h2>
  <p data-i18n="contact_body">{html_mod.escape(T['en']['about_contact_body'])}</p>
  <p><a class="pr-btn pr-btn-primary" href="mailto:idev10752@gmail.com">idev10752@gmail.com</a></p>
"""
    return head("about", i18n_all, "title", "meta_desc", ld) + body + tail(i18n_all)


def page_press(games, T):
    """dopresskit 様式のプレスキット。2026-08-14 にユーザー依頼で12言語化した
    （それまでは英語のみ）。文言は tools/pages_i18n.json の press_* が正本で、
    ここでは press_ 接頭辞を外して他ページと同じ i18n 機構に載せる。"""
    ios_n = sum(1 for g in games if g["ios"])
    rbx_n = sum(1 for g in games if g["roblox"])

    i18n_all = {}
    for L in LANGS:
        d = {k[len("press_"):]: v for k, v in T[L].items() if k.startswith("press_")}
        missing = {"title", "meta_desc", "h1", "lead", "v_plat"} - set(d)
        if missing:
            raise SystemExit("gen_pages: press_%s が pages_i18n.json の %s に無い"
                             % (sorted(missing)[0], L))
        # 実機数は生成時に差し込む（翻訳側は {ios}/{rbx} を残す約束）
        d["v_plat"] = d["v_plat"].format(ios=ios_n, rbx=rbx_n)
        i18n_all[L] = d

    rows = "\n".join(
        f'      <li><a href="../{g["slug"]}/">{html_mod.escape(g["title_en"])}</a>'
        + (f' · <a href="{g["ios"]}" target="_blank" rel="noopener">App Store</a>' if g["ios"] else "")
        + (f' · <a href="{g["roblox"]}" target="_blank" rel="noopener">Roblox</a>' if g["roblox"] else "")
        + "</li>"
        for g in games
    )
    en = i18n_all["en"]
    ld = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebPage",'
          f'"name":{json.dumps(en["title"], ensure_ascii=False)},"url":"{SITE}press/",'
          f'"description":{json.dumps(en["meta_desc"], ensure_ascii=False)},'
          '"about":{"@type":"Organization","name":"PixelRyu","url":"' + SITE + '",'
          '"logo":"' + SITE + 'icon.png","email":"idev10752@gmail.com",'
          '"foundingLocation":{"@type":"Country","name":"Japan"},'
          '"sameAs":["https://pixelryu.substack.com/","https://note.com/pixelryu",'
          '"https://www.youtube.com/@PixelRyu-Japan","https://x.com/PixelRyu10752"]}}</script>\n'
          '<script type="application/ld+json">{"@context":"https://schema.org","@type":"BreadcrumbList",'
          '"itemListElement":[{"@type":"ListItem","position":1,"name":"PixelRyu","item":"' + SITE + '"},'
          '{"@type":"ListItem","position":2,"name":"Press","item":"' + SITE + 'press/"}]}</script>')

    def e(k):
        return html_mod.escape(en[k])

    body = f"""
  <h1 data-i18n="h1">{e('h1')}</h1>
  <p class="pr-lead" data-i18n="lead">{e('lead')}</p>

  <h2 data-i18n="sec_fact">{e('sec_fact')}</h2>
  <div class="tester-card">
    <ul>
      <li><strong data-i18n="f_dev">{e('f_dev')}</strong> <span data-i18n="v_dev">{e('v_dev')}</span></li>
      <li><strong data-i18n="f_base">{e('f_base')}</strong> <span data-i18n="v_base">{e('v_base')}</span></li>
      <li><strong data-i18n="f_games">{e('f_games')}</strong> {len(games)}</li>
      <li><strong data-i18n="f_plat">{e('f_plat')}</strong> <span data-i18n="v_plat">{e('v_plat')}</span></li>
      <li><strong data-i18n="f_langs">{e('f_langs')}</strong> <span data-i18n="v_langs">{e('v_langs')}</span></li>
      <li><strong data-i18n="f_price">{e('f_price')}</strong> <span data-i18n="v_price">{e('v_price')}</span></li>
      <li><strong data-i18n="f_contact">{e('f_contact')}</strong> <a href="mailto:idev10752@gmail.com">idev10752@gmail.com</a></li>
      <li><strong data-i18n="f_site">{e('f_site')}</strong> <a href="{SITE}">pixelryu.github.io</a></li>
    </ul>
  </div>

  <h2 data-i18n="sec_history">{e('sec_history')}</h2>
  <div class="tester-card">
    <p data-i18n="hist1">{e('hist1')}</p>
    <p data-i18n="hist2">{e('hist2')}</p>
  </div>

  <h2 data-i18n="sec_games">{e('sec_games')}</h2>
  <div class="tester-card">
    <ul>
{rows}
    </ul>
  </div>

  <h2 data-i18n="sec_logo">{e('sec_logo')}</h2>
  <div class="tester-card">
    <p data-i18n="logo1">{e('logo1')}</p>
    <p><img src="../icon.webp" alt="PixelRyu" width="96" height="96" style="border-radius:50%"></p>
  </div>
"""
    return head("press", i18n_all, "title", "meta_desc", ld) + body + tail(i18n_all)


def main():
    games = extract_games()
    home = extract_home_i18n()
    T = json.load(open(I18N_PAGES_JSON, encoding="utf-8"))
    # トップの統計ラベルを about でも使う
    for L in LANGS:
        for k in ("stat_games", "stat_langs", "stat_platforms"):
            if k in home.get(L, {}):
                T[L][k] = home[L][k]

    out = {
        "games": page_games(games, T, home),
        "roblox": page_roblox(games, T, home),
        "support": page_support(T),
        "about": page_about(games, T),
        "press": page_press(games, T),
    }
    for slug, content in out.items():
        d = os.path.join(BASE, slug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ {slug}/index.html  ({len(content.splitlines())} 行)")
    print(f"抽出したゲーム: {len(games)} 作")


if __name__ == "__main__":
    main()
