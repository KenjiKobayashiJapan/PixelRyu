#!/usr/bin/env python3
"""Generate <app>/video.html promo-video pages + deploy the portrait (vertical) videos.

Each page shows the app icon + title, then the LANDSCAPE trailer (top) and the
PORTRAIT trailer(s) below. Apps whose vertical promo is a 3-part series show all
three; single-cut apps show one. Language follows the site (localStorage
pixelryu_lang_v2 || browser): Japanese shows the JA-subtitled cut, every other
language the EN-subtitled cut, where those exist (single-cut older apps use the one
available file).

Portrait videos are deployed under a uniform name: promotion_V_01.mp4 (+_ja),
promotion_V_02.mp4 (+_ja), promotion_V_03.mp4 (+_ja).

CounterParts is intentionally absent: it has no portrait promo video.

Run:  python3 tools/gen_video_pages.py
"""
import io, os, glob, shutil, json

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
REPO = os.path.normpath(os.path.join(ROOT, ".."))  # koba_game_01 (holds 00xx_<app>/store)
BCV = "20260618213000"   # breadcrumb.js cache key for the pages
VIDV = "20260618213000"  # cache key for the (re)deployed portrait videos

LANGUAGES = ('[{"code":"en","flag":"\\ud83c\\uddfa\\ud83c\\uddf8","name":"English"},'
 '{"code":"ja","flag":"\\ud83c\\uddef\\ud83c\\uddf5","name":"\\u65e5\\u672c\\u8a9e"},'
 '{"code":"zh","flag":"\\ud83c\\udde8\\ud83c\\uddf3","name":"\\u7b80\\u4f53\\u4e2d\\u6587"},'
 '{"code":"ko","flag":"\\ud83c\\uddf0\\ud83c\\uddf7","name":"\\ud55c\\uad6d\\uc5b4"},'
 '{"code":"hi","flag":"\\ud83c\\uddee\\ud83c\\uddf3","name":"\\u0939\\u093f\\u0928\\u094d\\u0926\\u0940"},'
 '{"code":"id","flag":"\\ud83c\\uddee\\ud83c\\udde9","name":"Bahasa Indonesia"},'
 '{"code":"de","flag":"\\ud83c\\udde9\\ud83c\\uddea","name":"Deutsch"},'
 '{"code":"fr","flag":"\\ud83c\\uddeb\\ud83c\\uddf7","name":"Fran\\u00e7ais"},'
 '{"code":"it","flag":"\\ud83c\\uddee\\ud83c\\uddf9","name":"Italiano"},'
 '{"code":"es","flag":"\\ud83c\\uddea\\ud83c\\uddf8","name":"Espa\\u00f1ol"},'
 '{"code":"pt","flag":"\\ud83c\\udde7\\ud83c\\uddf7","name":"Portugu\\u00eas"},'
 '{"code":"ru","flag":"\\ud83c\\uddf7\\ud83c\\uddfa","name":"\\u0420\\u0443\\u0441\\u0441\\u043a\\u0438\\u0439"}]')

SUB = {
 "en":"Promo videos","ja":"プロモーション動画","zh":"宣传视频","ko":"프로모션 영상",
 "hi":"प्रोमो वीडियो","id":"Video promosi","de":"Promo-Videos","fr":"Vidéos promo",
 "it":"Video promozionali","es":"Vídeos promocionales","pt":"Vídeos promocionais","ru":"Промо-видео",
}

# slug -> (Title, horizontal_en, horizontal_ja|None, src_subdir, [ (vert_src_en, vert_src_ja|None), ... ])
APPS = {
 "wagashi":            ("WAGASHI","promotion_H_story.mp4","promotion_H_story_ja.mp4","0012_wagashi",
                        [("promotion_V_01_en.mp4","promotion_V_01_ja.mp4"),("promotion_V_02_en.mp4","promotion_V_02_ja.mp4"),("promotion_V_03_en.mp4","promotion_V_03_ja.mp4")]),
 "tatami":             ("TATAMI","promotion_H_story.mp4","promotion_H_story_ja.mp4","0010_tatami",
                        [("promotion_V_01_en.mp4","promotion_V_01_ja.mp4"),("promotion_V_02_en.mp4","promotion_V_02_ja.mp4"),("promotion_V_03_en.mp4","promotion_V_03_ja.mp4")]),
 "temari":             ("TEMARI","promotion_H_story.mp4","promotion_H_story_ja.mp4","0009_temari",
                        [("promotion_V_1_en.mp4","promotion_V_1_ja.mp4"),("promotion_V_2_en.mp4","promotion_V_2_ja.mp4"),("promotion_V_3_en.mp4","promotion_V_3_ja.mp4")]),
 "bounce-cat":         ("Bounce Cat","promotion_H_story.mp4","promotion_H_story_ja.mp4","0008_bounce_cat",
                        [("promotion_V_01_en.mp4","promotion_V_01_ja.mp4"),("promotion_V_02_en.mp4","promotion_V_02_ja.mp4"),("promotion_V_03_en.mp4","promotion_V_03_ja.mp4")]),
 "hayate":             ("HAYATE","promotion_H_trailer_en.mp4","promotion_H_trailer_ja.mp4","0007_hayate",
                        [("promotion_V_ep1_en.mp4","promotion_V_ep1_ja.mp4"),("promotion_V_ep2_en.mp4","promotion_V_ep2_ja.mp4"),("promotion_V_ep3_en.mp4","promotion_V_ep3_ja.mp4")]),
 "sumlings":           ("Sumlings","promotion_H_story.mp4",None,"0006_sumlings",
                        [("promotion_V_01_en.mp4","promotion_V_01_ja.mp4"),("promotion_V_02_en.mp4","promotion_V_02_ja.mp4"),("promotion_V_03_en.mp4","promotion_V_03_ja.mp4")]),
 "parcel-pals":        ("Parcel Pals","promotion_H_story.mp4",None,"0005_parcel_pals",
                        [("promotion_V_01_en.mp4","promotion_V_01_ja.mp4"),("promotion_V_02_en.mp4","promotion_V_02_ja.mp4"),("promotion_V_03_en.mp4","promotion_V_03_ja.mp4")]),
 "issen":              ("ISSEN","promotion_H_story_full.mp4",None,"0004_issen",
                        [("promotion_V_01_en.mp4","promotion_V_01_ja.mp4"),("promotion_V_02_en.mp4","promotion_V_02_ja.mp4"),("promotion_V_03_en.mp4","promotion_V_03_ja.mp4")]),
 "hotaru":             ("HOTARU","promotion_H_01.mp4",None,"0003_hotaru",
                        [("promotion_V_01.mp4",None)]),
 "liquid-glow-cosmic": ("Liquid Glow","promotion_H_story.mp4","promotion_H_story_ja.mp4","0002_liquid_glow",
                        [("promotion_V_01.mp4",None)]),
 "mole-whack":         ("Mole Whack","promotion_H_compilation.mp4",None,"0001_first_trial",
                        [("promotion_V_01.mp4",None)]),
}

CSS = (
 "*{box-sizing:border-box}"
 "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',sans-serif;"
 "background:radial-gradient(ellipse at top,#10162e 0%,#0b1020 60%,#070b16 100%);color:#e4ebf5;margin:0;min-height:100vh}"
 ".container{max-width:860px;margin:0 auto;padding:26px 20px 64px;position:relative}"
 ".lang-switch{position:absolute;top:18px;right:18px}"
 ".lang-switch select{background:#0d1428;color:#e4ebf5;border:1px solid rgba(160,200,255,.25);border-radius:6px;"
 "padding:5px 10px;font-size:13px;font-family:inherit;cursor:pointer}"
 ".lang-switch select option{background:#0d1428;color:#e4ebf5}"
 ".vp-head{text-align:center;margin:20px 0 30px}"
 ".vp-icon{width:96px;height:96px;border-radius:22px;box-shadow:0 8px 30px rgba(0,0,0,.45)}"
 ".vp-title{font-size:34px;margin:14px 0 4px;font-weight:700;letter-spacing:.01em}"
 ".vp-sub{margin:0;color:#9fb0d0;font-size:15px}"
 ".vp-video{display:block;width:100%;background:#000;border-radius:14px;box-shadow:0 10px 36px rgba(0,0,0,.5)}"
 ".vp-h{max-width:760px;aspect-ratio:16/9;margin:0 auto 34px}"
 ".vp-vrow{display:flex;flex-wrap:wrap;gap:20px;justify-content:center;align-items:flex-start}"
 ".vp-v{flex:0 1 248px;max-width:300px;aspect-ratio:9/16}"
 "@media(max-width:600px){.vp-title{font-size:28px}.vp-v{flex-basis:78%}.lang-switch{top:14px;right:14px}}"
)

TPL = """<!DOCTYPE html>
<html lang="en">
<head>
<link rel="preconnect" href="https://www.googletagmanager.com" crossorigin>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-M5MH53Z8LM"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-M5MH53Z8LM');
</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Promo Videos | PixelRyu</title>
<meta name="description" content="Promotional videos for {title} by PixelRyu — landscape and portrait trailers.">
<link rel="canonical" href="https://pixelryu.github.io/{slug}/video.html">
<meta name="robots" content="index,follow">
<link rel="icon" type="image/png" href="https://pixelryu.github.io/{slug}/icon.png">
<link rel="apple-touch-icon" href="https://pixelryu.github.io/{slug}/icon.png">
<meta property="og:title" content="{title} — Promo Videos | PixelRyu">
<meta property="og:description" content="Landscape and portrait promo videos for {title} by PixelRyu.">
<meta property="og:image" content="https://pixelryu.github.io/{slug}/og.png">
<meta property="og:type" content="video.other">
<meta property="og:url" content="https://pixelryu.github.io/{slug}/video.html">
<style>{css}</style>
</head>
<body>
<div class="container">
  <div class="lang-switch">
    <select id="lang-select" aria-label="Language"></select>
  </div>
  <header class="vp-head">
    <img class="vp-icon" src="icon.png" alt="{title} icon" width="96" height="96">
    <h1 class="vp-title">{title}</h1>
    <p class="vp-sub" data-i18n="videos_sub">Promo videos</p>
  </header>
  <video id="promo-h" class="vp-video vp-h" controls playsinline preload="metadata" poster="og.png" aria-label="{title} landscape promo video">
    <source src="{h_en}" type="video/mp4">
  </video>
  <div class="vp-vrow">
{vertical_videos}
  </div>
</div>
<script>
  const LANGUAGES = {languages};
  const SUB = {sub_json};
  const i18n = {{}}; LANGUAGES.forEach(function(l){{ i18n[l.code] = {{ videos_sub: SUB[l.code] || SUB.en }}; }});
  const H_EN = "{h_en}", H_JA = {h_ja_js};
  const V_PARTS = {v_parts_json};
  const VIDV = "{vidv}";
  const LANG_STORAGE_KEY = 'pixelryu_lang_v2';

  function detectLang() {{
    try {{ var s = localStorage.getItem(LANG_STORAGE_KEY); if (s && i18n[s]) return s; }} catch (e) {{}}
    var raw = (navigator.language || 'en').toLowerCase();
    for (var i=0;i<LANGUAGES.length;i++) if (raw === LANGUAGES[i].code) return LANGUAGES[i].code;
    var head = raw.split(/[-_]/)[0];
    for (var j=0;j<LANGUAGES.length;j++) if (head === LANGUAGES[j].code) return LANGUAGES[j].code;
    return 'en';
  }}
  function setSrc(id, file) {{
    var v = document.getElementById(id); if (!v) return;
    var s = v.querySelector('source');
    if (s && s.getAttribute('src') !== file) {{ s.setAttribute('src', file); v.load(); }}
  }}
  function setLang(lang, persist) {{
    var dict = i18n[lang]; if (!dict) return;
    if (persist) {{ try {{ localStorage.setItem(LANG_STORAGE_KEY, lang); }} catch (e) {{}} }}
    document.documentElement.lang = lang;
    document.querySelectorAll('[data-i18n]').forEach(function(el){{
      var k = el.getAttribute('data-i18n'); if (k in dict) el.textContent = dict[k];
    }});
    var ja = (lang === 'ja');
    setSrc('promo-h', (ja && H_JA) ? H_JA : H_EN);
    V_PARTS.forEach(function(pt){{
      setSrc(pt.id, pt.base + ((ja && pt.ja) ? '_ja' : '') + '.mp4?v=' + VIDV);
    }});
    var sel = document.getElementById('lang-select'); if (sel) sel.value = lang;
  }}
  (function init() {{
    var sel = document.getElementById('lang-select');
    for (var i=0;i<LANGUAGES.length;i++) {{
      var o = document.createElement('option');
      o.value = LANGUAGES[i].code; o.textContent = LANGUAGES[i].flag + ' ' + LANGUAGES[i].name;
      sel.appendChild(o);
    }}
    setLang(detectLang(), true);
    sel.addEventListener('change', function(e){{ setLang(e.target.value, true); }});
  }})();
</script>
<script src="../breadcrumb.js?v={bcv}" defer></script>
</body>
</html>
"""

def jstr(v):
    return "null" if v is None else '"%s"' % v

def main():
    made = 0
    for slug, (title, h_en, h_ja, sub, parts) in APPS.items():
        appdir = os.path.join(ROOT, slug)
        # clean any previously-deployed portrait videos, then deploy the configured parts
        for old in glob.glob(os.path.join(appdir, "promotion_V*.mp4")):
            os.remove(old)
        v_parts = []
        vids_html = []
        for i, (ven, vja) in enumerate(parts, 1):
            base = "promotion_V_%02d" % i
            shutil.copyfile(os.path.join(REPO, sub, "store", ven), os.path.join(appdir, base + ".mp4"))
            has_ja = bool(vja)
            if has_ja:
                shutil.copyfile(os.path.join(REPO, sub, "store", vja), os.path.join(appdir, base + "_ja.mp4"))
            vid = "promo-v%d" % i
            v_parts.append({"id": vid, "base": base, "ja": has_ja})
            vids_html.append(
                '    <video id="%s" class="vp-video vp-v" controls playsinline preload="metadata" '
                'aria-label="%s portrait promo video %d">\n'
                '      <source src="%s.mp4?v=%s" type="video/mp4">\n'
                '    </video>' % (vid, title, i, base, VIDV))
        h_en_v = h_en + "?v=" + VIDV
        h_ja_v = (h_ja + "?v=" + VIDV) if h_ja else None
        html = TPL.format(
            title=title, slug=slug, css=CSS, languages=LANGUAGES,
            sub_json=json.dumps(SUB, ensure_ascii=False),
            vertical_videos="\n".join(vids_html),
            h_en=h_en_v, h_ja_js=jstr(h_ja_v),
            v_parts_json=json.dumps(v_parts), vidv=VIDV, bcv=BCV)
        io.open(os.path.join(appdir, "video.html"), "w", encoding="utf-8").write(html)
        print("  %-20s video.html + %d portrait video(s)%s" % (slug, len(parts), " (with ja)" if parts[0][1] else ""))
        made += 1
    print("done. %d video pages." % made)

if __name__ == "__main__":
    main()
