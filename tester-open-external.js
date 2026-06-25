/* tester-open-external.js — escape in-app browsers for Google Play closed-test sign-up.
 *
 * WHY: Google Play's closed-test opt-in (play.google.com/apps/testing/<pkg>) and the
 * store/details page of an unpublished app are visible ONLY to a signed-in, allowlisted
 * tester. LINE / Telegram (and FB / Instagram / X) open links in a custom WKWebView /
 * Android WebView whose cookie jar is ISOLATED from Safari/Chrome, so it carries none of
 * the user's Google session cookies. To that anonymous request Play returns its generic
 * 404 ("requested URL was not found") — which is exactly what testers see when they tap
 * the link from a chat. In a real browser (already signed in to Google) the same link works.
 *
 * FIX: get the user into the external default browser.
 *  - LINE: append the LINE-only parameter `openExternalBrowser=1` to the tester links and
 *    offer a one-tap "open this page in browser" anchor (gesture-driven <a> is the most
 *    reliably honored escape; the param is ignored harmlessly by every non-LINE app).
 *  - Telegram / other in-app browsers: there is no such parameter, so show instructions to
 *    use the browser's "Open in Safari / Open in browser" menu, plus a copy-URL button.
 *  Manual menu fallback is always mentioned because the LINE param is community-established
 *  (not formally contracted) and a minority of iOS cases are flaky.
 */
(function () {
  "use strict";
  var ua = navigator.userAgent || "";

  // --- named in-app browsers -------------------------------------------------
  var isLine = /\bLine\//i.test(ua);                       // LINE iOS & Android: "... Line/x.y.z"
  var isTelegram = /\bTelegram\b/i.test(ua);               // some Telegram builds expose it
  var isFB = /\bFB(AN|AV|_IAB|IOS)\b/i.test(ua);           // Facebook
  var isIG = /\bInstagram\b/i.test(ua);                    // Instagram
  var isTwitter = /\bTwitter\b/i.test(ua);                 // X / Twitter
  var isWeChat = /MicroMessenger/i.test(ua);               // WeChat

  // --- generic in-app webview heuristics (catch Telegram etc. when unnamed) ---
  var isIOS = /iPhone|iPod|iPad/i.test(ua);
  // Real iOS Safari always carries a "Safari" token + "Version/"; dedicated browsers use
  // CriOS/FxiOS/EdgiOS. A WebKit UA on iOS lacking all of those is a custom WKWebView.
  var iosInApp = isIOS && /AppleWebKit/i.test(ua) && !/Safari/i.test(ua) &&
                 !/CriOS|FxiOS|EdgiOS/i.test(ua);
  // Android in-app WebViews tag the UA with "; wv"; real Chrome for Android never does.
  var androidInApp = /\bwv\b/i.test(ua) || /; wv\)/i.test(ua);

  var inApp = isLine || isTelegram || isFB || isIG || isTwitter || isWeChat ||
              iosInApp || androidInApp;
  if (!inApp) return;

  // --- localized banner copy -------------------------------------------------
  var T = {
    en: { warn: "Tester sign-up does not work inside this in-app browser.", line: "Open this page in your browser", other: "Tap the menu and choose “Open in browser” / “Open in Safari”, then continue in a browser signed in to your Google account.", copy: "Copy link", copied: "Copied" },
    ja: { warn: "アプリ内ブラウザではテスター登録ができません。", line: "このページをブラウザで開く", other: "メニューから「ブラウザで開く / Safariで開く」を選び、Googleにログイン済みのブラウザ(Safari/Chrome)で続けてください。", copy: "リンクをコピー", copied: "コピーしました" },
    zh: { warn: "在此应用内置浏览器中无法完成测试员注册。", line: "在浏览器中打开此页面", other: "请点按菜单选择“在浏览器中打开 / 用 Safari 打开”，然后在已登录 Google 账号的浏览器中继续。", copy: "复制链接", copied: "已复制" },
    ko: { warn: "인앱 브라우저에서는 테스터 등록이 되지 않습니다.", line: "이 페이지를 브라우저에서 열기", other: "메뉴에서 ‘브라우저에서 열기 / Safari로 열기’를 선택한 뒤 Google 계정에 로그인된 브라우저에서 계속하세요.", copy: "링크 복사", copied: "복사됨" },
    hi: { warn: "इस इन-ऐप ब्राउज़र में टेस्टर साइन-अप काम नहीं करता।", line: "इस पेज को ब्राउज़र में खोलें", other: "मेन्यू से ‘ब्राउज़र में खोलें / Safari में खोलें’ चुनें, फिर अपने Google खाते में साइन-इन ब्राउज़र में जारी रखें।", copy: "लिंक कॉपी करें", copied: "कॉपी हुआ" },
    id: { warn: "Pendaftaran tester tidak berfungsi di browser dalam aplikasi ini.", line: "Buka halaman ini di browser", other: "Ketuk menu dan pilih “Buka di browser” / “Buka di Safari”, lalu lanjutkan di browser yang sudah login akun Google.", copy: "Salin tautan", copied: "Tersalin" },
    de: { warn: "Die Tester-Anmeldung funktioniert in diesem In-App-Browser nicht.", line: "Diese Seite im Browser öffnen", other: "Tippe auf das Menü und wähle „Im Browser öffnen“ / „In Safari öffnen“, dann weiter in einem bei Google angemeldeten Browser.", copy: "Link kopieren", copied: "Kopiert" },
    fr: { warn: "L’inscription testeur ne fonctionne pas dans ce navigateur intégré.", line: "Ouvrir cette page dans le navigateur", other: "Touchez le menu et choisissez « Ouvrir dans le navigateur » / « Ouvrir dans Safari », puis continuez dans un navigateur connecté à votre compte Google.", copy: "Copier le lien", copied: "Copié" },
    it: { warn: "L’iscrizione tester non funziona in questo browser in-app.", line: "Apri questa pagina nel browser", other: "Tocca il menu e scegli “Apri nel browser” / “Apri in Safari”, poi continua in un browser con l’account Google connesso.", copy: "Copia link", copied: "Copiato" },
    es: { warn: "El registro de probador no funciona en este navegador integrado.", line: "Abrir esta página en el navegador", other: "Toca el menú y elige “Abrir en el navegador” / “Abrir en Safari”, luego continúa en un navegador con tu cuenta de Google iniciada.", copy: "Copiar enlace", copied: "Copiado" },
    pt: { warn: "O cadastro de testador não funciona neste navegador integrado.", line: "Abrir esta página no navegador", other: "Toque no menu e escolha “Abrir no navegador” / “Abrir no Safari”, depois continue num navegador com a conta Google conectada.", copy: "Copiar link", copied: "Copiado" },
    ru: { warn: "Регистрация тестировщика не работает во встроенном браузере.", line: "Открыть эту страницу в браузере", other: "Откройте меню и выберите «Открыть в браузере» / «Открыть в Safari», затем продолжите в браузере с входом в аккаунт Google.", copy: "Копировать ссылку", copied: "Скопировано" }
  };
  function pickLang() {
    var l = "";
    try { l = localStorage.getItem("pixelryu_lang_v2") || ""; } catch (e) {}
    if (!T[l]) l = (navigator.language || "").slice(0, 2);
    if (!T[l]) l = (document.documentElement.getAttribute("lang") || "").slice(0, 2);
    return T[l] ? l : "en";
  }
  var t = T[pickLang()];

  function withParam(url) {
    if (url.indexOf("openExternalBrowser=") !== -1) return url;
    return url + (url.indexOf("?") === -1 ? "?" : "&") + "openExternalBrowser=1";
  }

  // Android only: wrap an https URL as an intent:// that hands the page off to the device's
  // DEFAULT browser (package-less = survives Chrome being absent). browser_fallback_url lets
  // Chrome recover when the intent can't resolve. Hosts that override shouldOverrideUrlLoading
  // (FB / IG / most "; wv" webviews) honor this; Telegram swallows it -> manual menu fallback.
  function intentUrl(url) {
    var base = url.split("#")[0]; // strip any fragment; "#Intent;" is the intent delimiter
    return "intent://" + base.replace(/^https?:\/\//i, "") +
      "#Intent;scheme=https;action=android.intent.action.VIEW;" +
      "category=android.intent.category.BROWSABLE;" +
      "S.browser_fallback_url=" + encodeURIComponent(base) + ";end";
  }

  function build() {
    var anchor = document.getElementById("tester-heading");
    var card = anchor ? (anchor.closest("section") || anchor.parentNode) : document.querySelector(".tester-card-base");
    if (!card) return;

    // LINE only: rewrite the tester links so a direct tap also escapes to Safari/Chrome.
    if (isLine) {
      var scope = card.querySelectorAll('a[href*="play.google.com"], a[href*="groups.google.com"]');
      for (var i = 0; i < scope.length; i++) {
        var h = scope[i].getAttribute("href") || "";
        if (/^https?:\/\//i.test(h)) scope[i].setAttribute("href", withParam(h));
      }
    }

    var b = document.createElement("div");
    b.setAttribute("role", "alert");
    b.style.cssText = "margin:0 0 16px;padding:12px 14px;border-radius:12px;background:#fff4e0;border:1px solid #e3b873;color:#5a3a12;font-size:14px;line-height:1.55;text-align:left";

    var msg = document.createElement("div");
    msg.textContent = "⚠️ " + t.warn;
    msg.style.fontWeight = "700";
    b.appendChild(msg);

    if (isLine) {
      var btn = document.createElement("a");
      btn.href = withParam(location.href);
      btn.textContent = t.line + " →";
      btn.style.cssText = "display:inline-block;margin-top:10px;padding:9px 18px;border-radius:999px;background:#06c755;color:#fff;font-weight:700;text-decoration:none";
      b.appendChild(btn);
    } else {
      // Android in-app webviews (Telegram / FB / IG / generic "; wv"): offer a one-tap
      // escape to the default browser via intent://. iOS WKWebView gets the manual route only
      // (intent:// is Android-only). The note + copy button below stay as the fallback.
      if (androidInApp) {
        var ob = document.createElement("a");
        ob.href = intentUrl(location.href); // re-open THIS page in the default external browser
        ob.textContent = t.line + " →";
        ob.style.cssText = "display:inline-block;margin-top:10px;margin-right:8px;padding:9px 18px;border-radius:999px;background:#5a3a12;color:#fff;font-weight:700;text-decoration:none";
        b.appendChild(ob);
      }
      var note = document.createElement("div");
      note.textContent = t.other;
      note.style.marginTop = androidInApp ? "10px" : "6px";
      b.appendChild(note);
      var cp = document.createElement("button");
      cp.type = "button";
      cp.textContent = t.copy;
      cp.style.cssText = "margin-top:10px;padding:9px 18px;border-radius:999px;background:#5a3a12;color:#fff;font-weight:700;border:0;cursor:pointer";
      cp.addEventListener("click", function () {
        var done = function () { cp.textContent = t.copied; };
        try {
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(location.href).then(done, done);
          } else { done(); }
        } catch (e) { done(); }
      });
      b.appendChild(cp);
    }
    card.insertBefore(b, card.firstChild);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }
})();
