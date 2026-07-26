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

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
LANGS = ["en", "ja", "zh", "ko", "hi", "id", "de", "fr", "it", "es", "pt", "ru"]
LOCALE = {"en": "en_US", "ja": "ja_JP", "zh": "zh_CN", "ko": "ko_KR", "hi": "hi_IN",
          "id": "id_ID", "de": "de_DE", "fr": "fr_FR", "it": "it_IT", "es": "es_ES",
          "pt": "pt_BR", "ru": "ru_RU"}
SITE = "https://pixelryu.github.io/"

GAMES = ["kado", "hanko", "okaeri", "shizuku", "senko", "wagashi", "counterparts", "temari",
         "tatami", "bounce-cat", "hoshikari", "hayate", "sumlings", "parcel-pals",
         "issen", "hotaru", "liquid-glow-cosmic", "liquid-glow", "mole-whack"]


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


def apply_i18n(src, d):
    # attr-type (e.g. <meta data-i18n-attr="content" data-i18n="meta_desc" ...>)
    def attr_repl(m):
        tag = m.group(0)
        km = re.search(r'data-i18n="([^"]+)"', tag)
        am = re.search(r'data-i18n-attr="([^"]+)"', tag)
        if not km or not am or km.group(1) not in d:
            return tag
        attr, val = am.group(1), esc_attr(d[km.group(1)])
        if re.search(r'\b%s="[^"]*"' % re.escape(attr), tag):
            return re.sub(r'\b%s="[^"]*"' % re.escape(attr), lambda _m: '%s="%s"' % (attr, val), tag, count=1)
        return tag[:-1] + ' %s="%s">' % (attr, val)
    src = re.sub(r'<\w+\b[^>]*\bdata-i18n-attr="[^"]+"[^>]*>', attr_repl, src)

    # text-type
    def text_repl(m):
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        if 'data-i18n-attr' in attrs:
            return m.group(0)
        km = re.search(r'\bdata-i18n="([^"]+)"', attrs)
        if not km or km.group(1) not in d:
            return m.group(0)
        return '<%s%s>%s</%s>' % (tag, attrs, esc_text(d[km.group(1)]), tag)
    return re.sub(r'<(\w+)((?:[^>]*\s)?data-i18n="[^"]+"[^>]*)>(.*?)</\1>', text_repl, src, flags=re.S)


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
            elif t == "FAQPage" and "faq_q1" in d:
                me = []
                for i in range(1, 6):
                    q, a = d.get("faq_q%d" % i), d.get("faq_a%d" % i)
                    if q and a:
                        me.append({"@type": "Question", "name": q,
                                   "acceptedAnswer": {"@type": "Answer", "text": a}})
                if me:
                    o["mainEntity"] = me
        new = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        return '<script type="application/ld+json">%s</script>' % new
    return re.sub(r'<script type="application/ld\+json">(.+?)</script>', repl, src, flags=re.S)


def absolutize(src, orig, L):
    # links to game-index pages / the homepage get the language suffix so a
    # language page links within its own language cluster; assets/overview/legal
    # links stay on the shared (en) resource.
    game_index = set(SITE + g + "/" for g in GAMES)
    def repl(m):
        pre, url, post = m.group(1), m.group(2), m.group(3)
        if re.match(r'(https?:)?//|^#|^mailto:|^tel:|^javascript:|^data:|^\{', url):
            return m.group(0)
        absu = urljoin(orig, url)
        if L != "en":
            if absu in game_index:
                absu = absu + L + "/"
            elif absu == SITE:
                absu = SITE + L + "/"
        return pre + absu + post
    return re.sub(r'(\b(?:href|src)=")([^"]+)(")', repl, src)


def rewire_switcher(src, orig, force_lang=None):
    # Language policy (2026-06-18 ユーザー指示): human-facing language is CLIENT-SIDE
    # and INHERITED across pages. Every page renders the stored-or-browser language on
    # load (initial display = browser setting; thereafter = the language carried over
    # from the previous page) and the switcher persists the choice IN PLACE — it does
    # NOT navigate to a per-language URL. The baked /<lang>/ pages still ship localized
    # STATIC html for crawlers (SEO), but for humans every page adapts the same way, so
    # English is always reachable and the chosen language follows you around.
    #
    # `force_lang` is kept for call-site compatibility but intentionally UNUSED: forcing
    # a page's language is exactly what made English unreachable and broke inheritance.
    # This function normalizes whatever switcher/init is present (navigating OR already
    # client-side, forced OR adaptive) to the client-side+adaptive form, so it is
    # idempotent across re-runs.
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
    else:
        # Template A (applyLang) — unify the legacy localStorage key, make the switcher
        # client-side, and detect the initial language (stored || browser).
        src = src.replace("localStorage.setItem('pixelryu_lang',",
                          "localStorage.setItem('pixelryu_lang_v2',")
        src = src.replace("localStorage.getItem('pixelryu_lang')",
                          "localStorage.getItem('pixelryu_lang_v2')")
        src = re.sub(nav_re,
                     "sel.addEventListener('change', function(e){ applyLang(e.target.value); });",
                     src)
        adaptive = ("var lang = 'en';"
                    " try{ lang = localStorage.getItem('pixelryu_lang_v2') || ''; }catch(e){}"
                    " if(!i18n[lang]){ var nv = (navigator.language||'en').slice(0,2);"
                    " lang = i18n[nv] ? nv : 'en'; }"
                    " sel.value = lang; applyLang(lang);")
        # only the forced one-liner matches; the adaptive block (with its try/if) does not.
        src = re.sub(r"var lang = '[a-z-]+'; sel\.value = lang; applyLang\(lang\);",
                     adaptive, src)
    return src


def gen_lang_page(src, i18n, L, orig, home_lang):
    d = i18n[L]
    langurl = orig + L + "/"
    out = src
    out = re.sub(r'<html lang="[^"]*">', '<html lang="%s">' % L, out, count=1)
    out = apply_i18n(out, d)
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
    if "hreflang=" not in out:
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
    targets = sys.argv[1:] or (["", *GAMES])
    targets = ["" if t in ("home", "homepage", "/") else t for t in targets]
    for t in targets:
        process(t)
    print("done.")
