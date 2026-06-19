/* PixelRyu — localize App Store links by the selected site language.
 *
 * A visitor reading the site in Japanese is sent to the Japanese App Store, a
 * German reader to the German store, and so on. Only the clickable <a> links to
 * apps.apple.com are rewritten; the JSON-LD download/canonical URLs are left
 * country-code-less ON PURPOSE (they are the canonical reference for crawlers).
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
  // zh is intentionally left blank: the apps are not published on the China App
  // Store and zh-Hans has no single unambiguous storefront, so Chinese stays
  // country-code-less and Apple auto-redirects the visitor to their own store.
  var STORE = {
    en: "us", ja: "jp", ko: "kr", hi: "in", id: "id",
    de: "de", fr: "fr", it: "it", es: "es", pt: "br", ru: "ru", zh: ""
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
