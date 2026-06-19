/* PixelRyu — point App Store badge links at a storefront that actually carries
 * the app, chosen PER APP and per site language.
 *
 * Two cases (verified 2026-06-20 with a live per-storefront HTTP check):
 *  - Apps with a full 12-language listing AND worldwide availability localize to
 *    the page language's storefront (a German reader -> the DE store, etc.).
 *    Confirmed: CounterParts (id535002008) returns 200 in all 12 storefronts.
 *  - Every other app has only English + Japanese listings and is NOT on sale in
 *    many storefronts (e.g. Sumlings 404s in DE/FR/IT/ES/RU). Forcing a storefront
 *    by page language there produced "page not found", so these route to the JP
 *    store for Japanese and the US (English) store for every other language —
 *    both always carry the apps. (owner instruction, 2026-06-20)
 *
 * The storefront is decided PER LINK from the Apple app id in the href, because
 * the top page shows badges for several apps at once. Only the clickable <a>
 * links to apps.apple.com are rewritten; the JSON-LD download/canonical URLs are
 * left country-code-less ON PURPOSE (they are the canonical reference for crawlers).
 *
 * Shared & self-contained — included via "/appstore-localize.js" on every page
 * that has App Store buttons (the top page and each app index, all 12 languages).
 * Follows the page's #lang-select and the shared key "pixelryu_lang_v2", so
 * switching the language re-points the buttons in place (no navigation).
 */
(function () {
  "use strict";

  var LANG_KEY = "pixelryu_lang_v2"; // shared with each page's own i18n + breadcrumb.js
  var CODES = ["en", "ja", "zh", "ko", "hi", "id", "de", "fr", "it", "es", "pt", "ru"];

  // Site language -> App Store storefront country code (full per-language map).
  // Used ONLY for apps in FULL_LOCALE_APP_IDS. zh -> "cn", pt -> "br".
  var FULL_STORE = {
    en: "us", ja: "jp", ko: "kr", hi: "in", id: "id",
    de: "de", fr: "fr", it: "it", es: "es", pt: "br", ru: "ru", zh: "cn"
  };

  // Apple app ids that may use FULL_STORE (12-language listing + available in
  // every one of those storefronts).
  //   535002008  = CounterParts — live, verified 200 in all 12 storefronts (2026-06-20).
  //   6781676381 = WAGASHI — 12 languages but still in review (no live link yet).
  //                Re-run the per-storefront HTTP check once it ships; if it is
  //                not on sale in some territory, drop it from here.
  var FULL_LOCALE_APP_IDS = { "535002008": 1, "6781676381": 1 };

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

  // The Apple numeric app id embedded in an apps.apple.com URL ("…/id6774177494").
  function appIdFromHref(href) {
    var m = href.match(/\/id(\d+)/);
    return m ? m[1] : null;
  }

  // Storefront code for a page language + the app the link points to.
  function storefrontFor(lang, appId) {
    if (appId && FULL_LOCALE_APP_IDS[appId]) {
      return FULL_STORE.hasOwnProperty(lang) ? FULL_STORE[lang] : "us";
    }
    // EN/JA-only apps: Japanese -> JP store, everything else -> US (English).
    return lang === "ja" ? "jp" : "us";
  }

  // Insert/replace the storefront country code in an apps.apple.com URL.
  // Idempotent: strips any existing 2-letter code first, then inserts the new one.
  function localizeUrl(href, cc) {
    href = href.replace(/(apps\.apple\.com)\/[a-z]{2}\/app\//, "$1/app/");
    if (cc) href = href.replace(/(apps\.apple\.com)\/app\//, "$1/" + cc + "/app/");
    return href;
  }

  function apply(lang) {
    var links = document.querySelectorAll('a[href*="apps.apple.com"]');
    for (var i = 0; i < links.length; i++) {
      var raw = links[i].getAttribute("href");
      if (!raw) continue;
      var cc = storefrontFor(lang, appIdFromHref(raw));
      links[i].setAttribute("href", localizeUrl(raw, cc));
    }
  }

  function run() {
    apply(detectLang());
    var sel = document.getElementById("lang-select");
    if (sel) {
      sel.addEventListener("change", function (e) {
        var v = e.target.value || detectLang();
        // Run after the page's own change handler (which may re-render content).
        setTimeout(function () { apply(v); }, 0);
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }
})();
