/* PixelRyu — point App Store badge links at a storefront that actually carries
 * the app, based on the selected site language.
 *
 * The apps are NOT distributed to every App Store territory, so forcing a
 * storefront by page language used to send visitors to a store where the
 * product 404s ("page not found") — e.g. the Russia (ru) or China (cn) store
 * has no PixelRyu apps. Fix: only confirmed-available storefronts are
 * localized — Japanese -> the JP store; everything else -> the US (English)
 * store, which always carries the apps. Where a localized store would 404,
 * English is the right fallback (owner instruction, 2026-06-20).
 *
 * Only the clickable <a> links to apps.apple.com are rewritten; the JSON-LD
 * download/canonical URLs are left country-code-less ON PURPOSE (they are the
 * canonical reference for crawlers).
 *
 * Shared & self-contained — included via the root-absolute path
 * "/appstore-localize.js" on every page that has App Store buttons (the top
 * page and each app index page, all 12 languages). It follows the page's
 * language selector (#lang-select) and the shared key "pixelryu_lang_v2", so
 * switching the language re-points the buttons in place (no navigation).
 */
(function () {
  "use strict";

  var LANG_KEY = "pixelryu_lang_v2"; // shared with each page's own i18n + breadcrumb.js
  var CODES = ["en", "ja", "zh", "ko", "hi", "id", "de", "fr", "it", "es", "pt", "ru"];

  // Site language -> App Store storefront country code.
  // ONLY storefronts where the apps are confirmed available are listed here;
  // any language not in this map falls back to "us" (English) in apply() below.
  // Rationale: the apps are not distributed to all territories, so previously
  // localizing pt->br, ru->ru, zh->cn, etc. produced "page not found" in stores
  // that carry no PixelRyu apps. The US (English) and JP stores always carry
  // them, so we keep en->us / ja->jp and send every other language to US English.
  // To re-enable a storefront, confirm the app is on sale there, then add it.
  var STORE = {
    en: "us", ja: "jp"
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

  // Insert/replace the storefront country code in an apps.apple.com URL.
  // Idempotent: strips any existing 2-letter code first, then inserts the new
  // one (or leaves the URL country-code-less when cc is "").
  function localizeUrl(href, cc) {
    href = href.replace(/(apps\.apple\.com)\/[a-z]{2}\/app\//, "$1/app/");
    if (cc) href = href.replace(/(apps\.apple\.com)\/app\//, "$1/" + cc + "/app/");
    return href;
  }

  function apply(lang) {
    var cc = STORE.hasOwnProperty(lang) ? STORE[lang] : "us";
    var links = document.querySelectorAll('a[href*="apps.apple.com"]');
    for (var i = 0; i < links.length; i++) {
      var raw = links[i].getAttribute("href");
      if (raw) links[i].setAttribute("href", localizeUrl(raw, cc));
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
