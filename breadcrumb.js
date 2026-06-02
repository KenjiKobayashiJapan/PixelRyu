/* PixelRyu breadcrumb — shared, self-contained, 12-language.
 *
 * Included on every sub-page (NOT the top page at the site root).
 * Auto-detects the app + page type from the URL, renders a localized
 * breadcrumb at the top of the page, and follows the page's language
 * selector (#lang-select) so it stays in sync with the rest of the UI.
 *
 * Hierarchy:  PixelRyu  ›  <App>  ›  <Page>
 *   - app index   ({app}/ or {app}/index.html):  PixelRyu › <App(current)>
 *   - leaf page   ({app}/overview|privacy|terms): PixelRyu › <App> › <Page(current)>
 *
 * The site is a user GitHub Pages site served at the root, and every
 * sub-page lives exactly one directory below it ({app}/*.html), so the
 * home link is always "../" and the app-index link is always "./".
 */
(function () {
  "use strict";

  var LANG_KEY = "pixelryu_lang_v2"; // shared with each page's own i18n
  var CODES = ["en", "ja", "zh", "ko", "hi", "id", "de", "fr", "it", "es", "pt", "ru"];

  // Home crumb label — brand name, identical in every language.
  var HOME_LABEL = "PixelRyu";

  // App display names (brand). `all` is the default; add per-language keys to override.
  var APP_NAMES = {
    "issen":       { all: "ISSEN" },
    "hotaru":      { all: "HOTARU" },
    "liquid-glow": { all: "Liquid Glow" },
    "mole-whack":  { all: "Mole Whack", ja: "モグラぽかぽか" },
    "parcel-pals": { all: "Parcel Pals", ja: "ふんわり配送便" },
    "sumlings":    { all: "Sumlings", ja: "サムリング" },
    "hayate":      { all: "HAYATE" }
  };

  // Leaf page labels (localized). Privacy/Terms match the legal-page generator
  // (tools/gen_legal_i18n.py LABELS); Overview matches the overview pages' page_label.
  var LEAF = {
    overview: {
      en: "Game Overview", ja: "ゲーム概要", zh: "游戏简介", ko: "게임 소개",
      hi: "गेम अवलोकन", id: "Ikhtisar Game", de: "Spielübersicht", fr: "Aperçu du jeu",
      it: "Panoramica del gioco", es: "Descripción del juego", pt: "Visão geral do jogo", ru: "Об игре"
    },
    privacy: {
      en: "Privacy Policy", ja: "プライバシーポリシー", zh: "隐私政策", ko: "개인정보 처리방침",
      hi: "गोपनीयता नीति", id: "Kebijakan Privasi", de: "Datenschutzerklärung", fr: "Politique de confidentialité",
      it: "Informativa sulla privacy", es: "Política de privacidad", pt: "Política de privacidade", ru: "Политика конфиденциальности"
    },
    terms: {
      en: "Terms of Service", ja: "利用規約", zh: "服务条款", ko: "서비스 이용약관",
      hi: "सेवा शर्तें", id: "Ketentuan Layanan", de: "Nutzungsbedingungen", fr: "Conditions d’utilisation",
      it: "Termini di servizio", es: "Términos del servicio", pt: "Termos de serviço", ru: "Условия использования"
    }
  };

  // Accessible label for the <nav>, localized.
  var ARIA = {
    en: "Breadcrumb", ja: "パンくずリスト", zh: "面包屑导航", ko: "이동 경로",
    hi: "ब्रेडक्रंब", id: "Tautan navigasi", de: "Brotkrümelnavigation", fr: "Fil d’Ariane",
    it: "Briciole di pane", es: "Ruta de navegación", pt: "Trilha de navegação", ru: "Хлебные крошки"
  };

  function detectLang() {
    try {
      var s = localStorage.getItem(LANG_KEY);
      if (s && CODES.indexOf(s) !== -1) return s;
    } catch (e) {}
    var raw = (navigator.language || "en").toLowerCase();
    if (CODES.indexOf(raw) !== -1) return raw;
    var head = raw.split(/[-_]/)[0];
    if (CODES.indexOf(head) !== -1) return head;
    return "en";
  }

  function pick(map, lang) {
    if (!map) return "";
    return map[lang] || map.all || map.en;
  }

  // Work out which app + leaf page we are on from the URL path.
  function detect() {
    var parts = location.pathname.split("/").filter(Boolean);
    var idx = -1;
    for (var i = 0; i < parts.length; i++) {
      if (APP_NAMES[parts[i]]) { idx = i; break; }
    }
    if (idx === -1) return null; // not an app sub-page → no breadcrumb
    var app = parts[idx];
    var file = parts[idx + 1] || ""; // "" => app index served from a trailing slash
    var leaf = null;
    if (file.indexOf("overview") === 0) leaf = "overview";
    else if (file.indexOf("privacy") === 0) leaf = "privacy";
    else if (file.indexOf("terms") === 0) leaf = "terms";
    // "" or index.html (or anything else) => treat as the app index
    return { app: app, leaf: leaf };
  }

  function injectStyle() {
    if (document.getElementById("pr-breadcrumb-style")) return;
    var css =
      // The breadcrumb and the language switcher share ONE top bar on every page,
      // in normal flow, so the order (breadcrumb left, switcher right) and the
      // layout are identical everywhere and nothing overlaps. On narrow screens
      // only the switcher drops to a second line — the breadcrumb never wraps.
      "#pr-topbar{display:flex;flex-wrap:wrap;align-items:center;column-gap:14px;row-gap:8px;margin:0 0 22px;width:100%;box-sizing:border-box;}" +
      "#pr-topbar .lang-switch{position:static;top:auto;right:auto;left:auto;bottom:auto;margin:0 0 0 auto;flex:0 0 auto;text-align:right;}" +
      ".breadcrumb{font-size:13px;line-height:1.5;opacity:.85;font-family:inherit;white-space:nowrap;flex:0 0 auto;}" +
      ".breadcrumb ol{list-style:none;margin:0;padding:0;display:flex;flex-wrap:nowrap;align-items:center;gap:4px 6px;white-space:nowrap;}" +
      ".breadcrumb li{display:flex;align-items:center;gap:4px 6px;}" +
      ".breadcrumb a{color:inherit;text-decoration:none;opacity:.85;}" +
      ".breadcrumb a:hover{opacity:1;text-decoration:underline;}" +
      ".breadcrumb .sep{opacity:.5;}" +
      ".breadcrumb [aria-current='page']{font-weight:600;opacity:1;}";
    var st = document.createElement("style");
    st.id = "pr-breadcrumb-style";
    st.textContent = css;
    document.head.appendChild(st);
  }

  var info = detect();

  function crumbs(lang) {
    var list = [{ label: HOME_LABEL, href: "../" }]; // PixelRyu (home)
    var appLabel = pick(APP_NAMES[info.app], lang);
    if (info.leaf) {
      list.push({ label: appLabel, href: "./" });        // app index
      list.push({ label: pick(LEAF[info.leaf], lang) }); // current leaf
    } else {
      list.push({ label: appLabel });                    // app index = current page
    }
    return list;
  }

  function render(nav, lang) {
    var items = crumbs(lang);
    var ol = document.createElement("ol");
    items.forEach(function (c, i) {
      var li = document.createElement("li");
      if (i > 0) {
        var sep = document.createElement("span");
        sep.className = "sep";
        sep.setAttribute("aria-hidden", "true");
        sep.textContent = "›";
        li.appendChild(sep);
      }
      if (c.href) {
        var a = document.createElement("a");
        a.href = c.href;
        a.textContent = c.label;
        li.appendChild(a);
      } else {
        var span = document.createElement("span");
        span.setAttribute("aria-current", "page");
        span.textContent = c.label;
        li.appendChild(span);
      }
      ol.appendChild(li);
    });
    nav.innerHTML = "";
    nav.setAttribute("aria-label", ARIA[lang] || ARIA.en);
    nav.appendChild(ol);
  }

  function mount() {
    if (!info) return; // not an app sub-page → render nothing
    injectStyle();
    var topbar = document.getElementById("pr-topbar");
    if (!topbar) {
      topbar = document.createElement("div");
      topbar.id = "pr-topbar";
      var nav = document.createElement("nav");
      nav.id = "breadcrumb";
      nav.className = "breadcrumb";
      topbar.appendChild(nav);
      // Relocate the page's existing language switcher next to the breadcrumb so
      // every page shows the same "breadcrumb | switcher" bar. The <select> keeps
      // its id and event listeners when moved, so the page's own i18n still works.
      var ls = document.querySelector(".lang-switch");
      if (ls) topbar.appendChild(ls);
      // Insert at the top of the page's main content wrapper (the content card on
      // app pages, the document body on legal pages) — normal flow, no overlap.
      var host = document.querySelector(".container") || document.body;
      host.insertBefore(topbar, host.firstChild);
    }
    var navEl = document.getElementById("breadcrumb");
    navEl.className = "breadcrumb";
    var lang = detectLang();
    render(navEl, lang);
    var sel = document.getElementById("lang-select");
    if (sel) {
      sel.addEventListener("change", function (e) {
        render(navEl, e.target.value || detectLang());
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount);
  } else {
    mount();
  }
})();
