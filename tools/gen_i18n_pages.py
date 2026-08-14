#!/usr/bin/env python3
"""Generate per-language static pages for multilingual SEO (hreflang).

Each game page (and the homepage) is a single English-static file with a JS i18n
object that swaps text client-side. Search engines only index the static English,
so 11 language markets are invisible. This generator renders each language to its
own static URL (e.g. temari/de/index.html) with the content baked in + reciprocal
hreflang + canonical, so every language can rank in its market.

Usage:  python3 tools/gen_i18n_pages.py [slug ...]
        (no args = all pages: homepage + every game index)
Idempotent: regenerates the <slug>/<lang>/ dirs and rewrites the en page's
hreflang + language-switcher each run.
"""
import os, re, sys, json, html, subprocess, tempfile
from urllib.parse import urljoin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shell_i18n import SHELL, check as shell_i18n_check   # 共通シェルの12言語辞書（正本）

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
LANGS = ["en", "ja", "zh", "ko", "hi", "id", "de", "fr", "it", "es", "pt", "ru"]
LOCALE = {"en": "en_US", "ja": "ja_JP", "zh": "zh_CN", "ko": "ko_KR", "hi": "hi_IN",
          "id": "id_ID", "de": "de_DE", "fr": "fr_FR", "it": "it_IT", "es": "es_ES",
          "pt": "pt_BR", "ru": "ru_RU"}
SITE = "https://pixelryu.github.io/"

GAMES = ["kado", "hanko", "okaeri", "shizuku", "senko", "wagashi", "counterparts", "temari",
         "tatami", "bounce-cat", "hoshikari", "hayate", "sumlings", "parcel-pals",
         "issen", "hotaru", "liquid-glow-cosmic", "liquid-glow", "mole-whack"]

# ゲームではないサイトセクション（2026-08 刷新で新設）。
# ここに入れると (a) 12言語ページが生成され (b) 言語ページ間のリンクが同じ言語に閉じる。
# press は当初「メディア向けだから英語のみ」としていたが、2026-08-14 にユーザー依頼で
# 12言語化した（海外メディア／配信者は英語圏だけではない）。
PAGES = ["games", "roblox", "support", "about", "press"]


def esc_text(s):
    return html.escape(s, quote=False)


def esc_attr(s):
    return html.escape(s, quote=True)


def extract_i18n(src):
    # game pages use quoted keys, the homepage uses unquoted JS keys — eval with
    # Node so both parse correctly (our own source; safe to eval).
    m = re.search(r'const i18n\s*=\s*\{', src)
    start = m.end() - 1
    depth = 0
    obj = None
    for i in range(start, len(src)):
        if src[i] == '{':
            depth += 1
        elif src[i] == '}':
            depth -= 1
            if depth == 0:
                obj = src[start:i + 1]
                break
    if obj is None:
        raise RuntimeError("i18n object not balanced")
    try:
        return json.loads(obj)
    except Exception:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write("const i18n = " + obj + ";\nprocess.stdout.write(JSON.stringify(i18n));")
            tmp = f.name
        try:
            out = subprocess.run(["node", tmp], capture_output=True, text=True)
            if out.returncode != 0:
                raise RuntimeError("node parse failed: " + out.stderr)
            return json.loads(out.stdout)
        finally:
            os.unlink(tmp)


def hreflang_block(orig):
    rows = []
    for l in LANGS:
        href = orig + (l + "/" if l != "en" else "")
        rows.append('<link rel="alternate" hreflang="%s" href="%s">' % (l, href))
    rows.append('<link rel="alternate" hreflang="x-default" href="%s">' % orig)
    return "\n".join(rows)


def apply_i18n(src, d, key_attr="data-i18n"):
    """`<key_attr>` を持つ要素を辞書 d の訳で置き換える。
    key_attr="data-pr-i18n" で共通シェル（ヘッダー/フッター）にも同じ機構を使う。
    シェルはページ辞書と名前空間が別（tools/shell_i18n.py が正本）。"""
    attr_attr = key_attr + "-attr"
    # attr-type (e.g. <meta data-i18n-attr="content" data-i18n="meta_desc" ...>)
    def attr_repl(m):
        tag = m.group(0)
        km = re.search(r'%s="([^"]+)"' % key_attr, tag)
        am = re.search(r'%s="([^"]+)"' % attr_attr, tag)
        if not km or not am or km.group(1) not in d:
            return tag
        attr, val = am.group(1), esc_attr(d[km.group(1)])
        if re.search(r'\b%s="[^"]*"' % re.escape(attr), tag):
            return re.sub(r'\b%s="[^"]*"' % re.escape(attr), lambda _m: '%s="%s"' % (attr, val), tag, count=1)
        return tag[:-1] + ' %s="%s">' % (attr, val)
    src = re.sub(r'<\w+\b[^>]*\b%s="[^"]+"[^>]*>' % attr_attr, attr_repl, src)

    # text-type
    def text_repl(m):
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        if attr_attr in attrs:
            # 属性側を訳す要素（例: aria-label 付きボタン）でも、その中の子要素は訳す。
            # ここで丸ごと返すと re.sub がマッチ末尾から再開するため、内側の
            # <span data-pr-i18n="..."> に二度と到達しない（英語のまま残る）。
            return '<%s%s>%s</%s>' % (tag, attrs, apply_i18n(inner, d, key_attr), tag)
        km = re.search(r'\b%s="([^"]+)"' % key_attr, attrs)
        if not km or km.group(1) not in d:
            return m.group(0)
        return '<%s%s>%s</%s>' % (tag, attrs, esc_text(d[km.group(1)]), tag)
    return re.sub(r'<(\w+)((?:[^>]*\s)?%s="[^"]+"[^>]*)>(.*?)</\1>' % key_attr,
                  text_repl, src, flags=re.S)


def transform_jsonld(src, d, langurl, home_lang):
    def repl(m):
        try:
            obj = json.loads(m.group(1))
        except Exception:
            return m.group(0)
        items = obj if isinstance(obj, list) else [obj]
        for o in items:
            t = o.get("@type")
            if t == "VideoGame":
                o["url"] = langurl
                if "meta_desc" in d:
                    o["description"] = d["meta_desc"]
            elif t == "BreadcrumbList":
                for it in o.get("itemListElement", []):
                    if it.get("position") == 1:
                        it["item"] = home_lang
                    elif it.get("position") == 2:
                        it["item"] = langurl
            elif t == "FAQPage":
                # ゲームページは faq_q1..q5、/support/ は q1..q6 のキー体系
                me = []
                for prefix, n in (("faq_q%d", 6), ("q%d", 7)):
                    for i in range(1, n):
                        q = d.get(prefix % i)
                        a = d.get(prefix.replace("q", "a") % i)
                        if q and a:
                            me.append({"@type": "Question", "name": q,
                                       "acceptedAnswer": {"@type": "Answer", "text": a}})
                    if me:
                        break
                if me:
                    o["mainEntity"] = me
            elif t in ("CollectionPage", "AboutPage", "ContactPage", "WebPage", "ItemList"):
                # 新設セクション（/games/ /roblox/ /support/ /about/）。
                # url と description を言語版へ寄せないと、各言語ページが英語 URL を
                # 構造化データで主張し続ける（重複判定の再発リスク）。
                if "url" in o:
                    o["url"] = langurl
                if "meta_desc" in d and "description" in o:
                    o["description"] = d["meta_desc"]
                if "title" in d and "name" in o:
                    o["name"] = d["title"]
        new = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        return '<script type="application/ld+json">%s</script>' % new
    return re.sub(r'<script type="application/ld\+json">(.+?)</script>', repl, src, flags=re.S)


ASSET_EXT = (".css", ".js", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg",
             ".ico", ".mp4", ".webm", ".woff", ".woff2")


def absolutize(src, orig, L):
    # links to game-index pages / the homepage get the language suffix so a
    # language page links within its own language cluster; assets/overview/legal
    # links stay on the shared (en) resource.
    #
    # ASSETS ARE THE EXCEPTION and stay RELATIVE (2026-08-13). A language mirror sits
    # exactly one directory below its source page, so "../" + the original relative path
    # always resolves. Absolutizing them made every mirror unviewable until deploy —
    # css/js/images pointed at production URLs that do not exist yet, so opening
    # /hi/index.html locally rendered as bare unstyled HTML. Relative paths work both
    # locally and in production; canonical/hreflang/og:* stay absolute (they are not
    # matched here: those live in <meta content=...>, and page links below stay absolute).
    game_index = set(SITE + g + "/" for g in GAMES + PAGES)
    def repl(m):
        pre, url, post = m.group(1), m.group(2), m.group(3)
        if re.match(r'(https?:)?//|^#|^mailto:|^tel:|^javascript:|^data:|^\{', url):
            return m.group(0)
        if not url.startswith("/") and url.split("?")[0].lower().endswith(ASSET_EXT):
            return pre + "../" + url + post
        absu = urljoin(orig, url)
        if L != "en":
            if absu in game_index:
                absu = absu + L + "/"
            elif absu == SITE:
                absu = SITE + L + "/"
        return pre + absu + post
    # 共通フッターの言語リンクだけは先に絶対URLへ固定する。英語エントリの href は
    # "../kado/" のようにゲーム索引と同形で、下の repl が言語サフィックスを足してしまい
    # 「English を押すと同じ言語ページに戻る」状態になる（しかも site.js が 'en' を保存
    # するので、以後どのページも英語で描画される）。
    def lang_link(m):
        pre, url, post = m.group(1), m.group(2), m.group(3)
        if re.match(r'(https?:)?//|^#|^mailto:', url):
            return m.group(0)
        return pre + urljoin(orig, url) + post
    src = re.sub(r'(<a [^>]*?\bhref=")([^"]*)(")(?=[^>]*\bdata-pr-lang=")', lang_link, src)
    return re.sub(r'(\b(?:href|src)=")([^"]+)(")', repl, src)


def rewire_switcher(src, orig, force_lang=None):
    # Language policy — TWO layers, deliberately different. Both must hold at once.
    #
    #  * HUMANS (2026-06-18 ユーザー指示): client-side and INHERITED across pages. A
    #    stored choice always wins, the switcher persists in place (it does NOT navigate
    #    to a per-language URL), so English stays reachable and the chosen language
    #    follows you around.
    #
    #  * CRAWLERS (2026-07-26 fix): Googlebot EXECUTES JavaScript. A baked /<lang>/ page
    #    that re-detects the language on load therefore renders as ENGLISH for Google and
    #    collapses into a byte-identical duplicate of the canonical page — proven with
    #    headless Chrome: /kado/, /kado/ja/ and /kado/de/ rendered to the same visible
    #    text (similarity 1.0000). That silently killed all 187 localized URLs and is the
    #    source of Search Console's "duplicate, Google chose a different canonical".
    #    Each baked page now PINS its own language via PAGE_LANG.
    #
    # PAGE_LANG is consulted AFTER localStorage but BEFORE navigator.language:
    #   - after localStorage  -> a human's explicit choice still wins => the 2026-06-18
    #                            "language sticking" bug cannot come back.
    #   - before navigator    -> a crawler (no storage, navigator=en-US) on /kado/ja/
    #                            gets Japanese. Putting it after navigator would leave
    #                            the bug fully intact, so the order matters.
    #
    # `force_lang` = the language of the page being generated. None or "en" (the
    # canonical entry page) stays purely browser-adaptive, so "initial display = browser
    # language" still holds where the user actually lands.
    page_lang = force_lang if (force_lang and force_lang != "en") else None

    nav_re = (r"sel\.addEventListener\('change',\s*function\(e\)\{var v=e\.target\.value;"
              r"window\.location\.href = [^;]*?;\}\);")
    if "function setLang(" in src:
        # Template B (setLang/detectLang, key 'pixelryu_lang_v2')
        src = re.sub(nav_re,
                     "sel.addEventListener('change', function(e){ setLang(e.target.value, true); });",
                     src)
        # forced or bare init -> adaptive + persist (matches setLang('xx'[,true]) and
        # setLang(detectLang()[,true]); never matches the switcher's e.target.value).
        src = re.sub(r"setLang\((?:'[a-z-]+'|detectLang\(\))(?:,\s*true)?\);",
                     "setLang(detectLang(), true);", src)
        # PAGE_LANG: strip any previous injection first, then re-add. Both injected forms
        # live on a line of their own, so line-wise removal is exact and re-runs are
        # idempotent (and the en page is left clean because page_lang is None there).
        src = re.sub(r"(?m)^[ \t]*var PAGE_LANG = '[a-z-]+';[ \t]*\n", "", src)
        src = re.sub(r"(?m)^[ \t]*if \(PAGE_LANG && i18n\[PAGE_LANG\]\) return PAGE_LANG;[ \t]*\n",
                     "", src)
        if page_lang:
            def _declare(m):
                return "%svar PAGE_LANG = %r;\n%s" % (m.group(1), page_lang, m.group(0))
            src, n_decl = re.subn(r"(?m)^([ \t]*)function detectLang\(\) \{[ \t]*\n",
                                  _declare, src, count=1)
            # Anchor on the navigator.language line rather than the localStorage block:
            # the storage read exists in both a one-line and a multi-line form across the
            # hand-authored sources, but this line is byte-identical everywhere, and
            # inserting *before* it puts PAGE_LANG in exactly the right priority slot
            # (after localStorage, before navigator).
            def _consult(m):
                return "%sif (PAGE_LANG && i18n[PAGE_LANG]) return PAGE_LANG;\n%s" % (m.group(1), m.group(0))
            src, n_use = re.subn(
                r"(?m)^([ \t]*)const raw = \(navigator\.language \|\| 'en'\)\.toLowerCase\(\);\n",
                _consult, src, count=1)
            if not (n_decl and n_use):
                raise SystemExit(
                    "gen_i18n_pages: PAGE_LANG injection failed for %r (decl=%d use=%d). "
                    "The detectLang() template changed — fix this generator, do NOT hand-edit "
                    "the generated pages." % (force_lang, n_decl, n_use))
    else:
        # Template A (applyLang) — unify the legacy localStorage key, make the switcher
        # client-side, and detect the initial language (stored || PAGE_LANG || browser).
        src = src.replace("localStorage.setItem('pixelryu_lang',",
                          "localStorage.setItem('pixelryu_lang_v2',")
        src = src.replace("localStorage.getItem('pixelryu_lang')",
                          "localStorage.getItem('pixelryu_lang_v2')")
        src = re.sub(nav_re,
                     "sel.addEventListener('change', function(e){ applyLang(e.target.value); });",
                     src)
        decl = ("var PAGE_LANG = %r; " % page_lang) if page_lang else ""
        pin = (" if(!i18n[lang] && i18n[PAGE_LANG]){ lang = PAGE_LANG; }") if page_lang else ""
        adaptive = (decl +
                    "var lang = 'en';"
                    " try{ lang = localStorage.getItem('pixelryu_lang_v2') || ''; }catch(e){}"
                    + pin +
                    " if(!i18n[lang]){ var nv = (navigator.language||'en').slice(0,2);"
                    " lang = i18n[nv] ? nv : 'en'; }"
                    " sel.value = lang; applyLang(lang);")
        # Matches the forced one-liner AND any already-rewritten adaptive block (with or
        # without a previous PAGE_LANG), so the whole init is rebuilt from scratch and
        # re-runs neither duplicate nor strand the declaration.
        src, n = re.subn(
            r"(?:var PAGE_LANG = '[a-z-]+'; )?var lang = '[a-z-]+';[^\n]*?"
            r"sel\.value = lang; applyLang\(lang\);",
            lambda m: adaptive, src, count=1)
        if not n:
            raise SystemExit(
                "gen_i18n_pages: applyLang init block not found (%r). The template changed "
                "— fix this generator, do NOT hand-edit the generated pages." % force_lang)
    return src


def gen_lang_page(src, i18n, L, orig, home_lang):
    d = i18n[L]
    langurl = orig + L + "/"
    out = src
    out = re.sub(r'<html lang="[^"]*">', '<html lang="%s">' % L, out, count=1)
    out = apply_i18n(out, d)
    # 共通シェル（ヘッダー/フッター/Follow）も静的に焼き込む。
    # site.js でも実行時に同じ辞書を当てるが、AIクローラ/Googlebot 対策として
    # HTML 側にも各言語の文言を残す必要がある（JS 非実行のクローラがいる）。
    out = apply_i18n(out, SHELL[L], "data-pr-i18n")
    out = out.replace('<link rel="canonical" href="%s">' % orig,
                      '<link rel="canonical" href="%s">\n%s' % (langurl, hreflang_block(orig)), 1)
    for prop, key in [('og:title', 'title'), ('og:description', 'meta_desc'),
                      ('og:image:alt', 'title'), ('twitter:title', 'title'),
                      ('twitter:description', 'meta_desc'), ('twitter:image:alt', 'title')]:
        val = esc_attr(d[key])
        out = re.sub(r'(<meta (?:property|name)="%s" content=")[^"]*(">)' % re.escape(prop),
                     lambda m, v=val: m.group(1) + v + m.group(2), out, count=1)
    out = out.replace('<meta property="og:url" content="%s">' % orig,
                      '<meta property="og:url" content="%s">' % langurl, 1)
    out = re.sub(r'(<meta property="og:locale" content=")[^"]*(">)',
                 lambda m: m.group(1) + LOCALE[L] + m.group(2), out, count=1)
    out = transform_jsonld(out, d, langurl, home_lang)
    out = absolutize(out, orig, L)
    out = re.sub(r"'([\w.\-]+\.mp4\?v=\d+)'", lambda m: "'" + orig + m.group(1) + "'", out)
    out = rewire_switcher(out, orig, L)
    return out


def modify_en_page(src, orig):
    out = src
    # ★ゲートは <link rel="alternate"> の有無で見ること。単に "hreflang=" を探すと、
    #   共通フッターの言語リンク <a hreflang="ja"> に反応して常に真になり、
    #   hreflang 注釈が二度と挿入されなくなる（片方向 hreflang ＝ Google に無視される）。
    if '<link rel="alternate" hreflang=' not in out:
        out = out.replace('<link rel="canonical" href="%s">' % orig,
                          '<link rel="canonical" href="%s">\n%s' % (orig, hreflang_block(orig)), 1)
    # Normalize the en/canonical page to the client-side + adaptive switcher (see
    # rewire_switcher): initial display follows the browser/stored language, the
    # switcher persists the choice in place, and the inherited language carries over.
    out = rewire_switcher(out, orig)
    return out


def process(slug):
    rel = (slug + "/index.html") if slug else "index.html"
    path = os.path.join(ROOT, rel)
    src = open(path, encoding="utf-8").read()
    # idempotency: strip any hreflang block from a previous run before regenerating
    src = re.sub(r'\n?<link rel="alternate" hreflang="[^"]*" href="[^"]*">', "", src)
    i18n = extract_i18n(src)
    orig = SITE + (slug + "/" if slug else "")
    # generate non-en language pages
    n = 0
    for L in LANGS:
        if L == "en":
            continue
        home_lang = SITE + (L + "/")
        page = gen_lang_page(src, i18n, L, orig, home_lang)
        outdir = os.path.join(ROOT, slug, L) if slug else os.path.join(ROOT, L)
        os.makedirs(outdir, exist_ok=True)
        open(os.path.join(outdir, "index.html"), "w", encoding="utf-8").write(page)
        n += 1
    # rewrite the en page (hreflang + navigating switcher)
    open(path, "w", encoding="utf-8").write(modify_en_page(src, orig))
    print("  %-20s -> %d lang pages + en updated" % (slug or "(home)", n))


if __name__ == "__main__":
    targets = sys.argv[1:] or (["", *GAMES, *PAGES])
    # 先に全対象の言語辞書の完全性を確かめる（preflight）。
    # 途中で KeyError を出すと「ja..pt は新版・ru は旧版」という部分更新状態で止まり、
    # 生成物が壊れたままデプロイされうるため、1ファイルも書く前に落とす。
    shell_i18n_check()
    _missing = ["shell_i18n: 言語が足りない -> %s" % ",".join(L for L in LANGS if L not in SHELL)] \
        if [L for L in LANGS if L not in SHELL] else []
    for _t in ["" if t in ("home", "homepage", "/") else t for t in targets]:
        _rel = (_t + "/index.html") if _t else "index.html"
        _p = os.path.join(ROOT, _rel)
        if not os.path.exists(_p):
            _missing.append("%s: ファイルが無い" % _rel)
            continue
        try:
            _d = extract_i18n(open(_p, encoding="utf-8").read())
        except Exception as e:
            _missing.append("%s: i18n を読めない (%s)" % (_rel, e))
            continue
        _lack = [L for L in LANGS if L not in _d]
        if _lack:
            _missing.append("%s: 言語が足りない -> %s" % (_rel, ",".join(_lack)))
    if _missing:
        print("preflight 失敗（1ファイルも書いていない）:")
        for m in _missing:
            print("   ", m)
        raise SystemExit(1)

    targets = ["" if t in ("home", "homepage", "/") else t for t in targets]
    for t in targets:
        process(t)
    print("done.")
