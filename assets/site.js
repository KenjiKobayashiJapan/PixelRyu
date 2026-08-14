/* PixelRyu — site.js
   共通の軽量スクリプト。依存なし。
   1) スクロール出現 2) ストアクリック計測(GA4) 3) モバイルメニューの外側クリック
   4) ナビの現在地 5) 共通シェルの多言語化 6) フッター言語リンクの選択保存
   計測は Consent Mode default=denied のまま動く（Cookie は発行されない）。 */
(function () {
  'use strict';

  /* ---- 1. スクロール出現 ---------------------------------- */
  var reveals = document.querySelectorAll('.pr-reveal');
  if (reveals.length) {
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce || !('IntersectionObserver' in window)) {
      for (var i = 0; i < reveals.length; i++) reveals[i].classList.add('is-visible');
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { e.target.classList.add('is-visible'); io.unobserve(e.target); }
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });
      for (var j = 0; j < reveals.length; j++) io.observe(reveals[j]);
    }
  }

  /* ---- 2. ストアクリック計測 ------------------------------ */
  /* href からストア種別を判定するので、既存のバッジHTMLに属性を足さなくても動く。 */
  function storeOf(href) {
    if (!href) return null;
    if (href.indexOf('apps.apple.com') > -1) return 'appstore';
    if (href.indexOf('play.google.com/store/apps/details') > -1) return 'googleplay';
    if (href.indexOf('play.google.com/apps/testing') > -1) return 'googleplay_test';
    if (href.indexOf('roblox.com/games/') > -1) return 'roblox';
    return null;
  }
  function gameOf(el) {
    var card = el.closest ? el.closest('[data-game]') : null;
    if (card && card.getAttribute('data-game')) return card.getAttribute('data-game');
    var m = location.pathname.match(/^\/([a-z0-9-]+)\//);
    if (m && ['ja','zh','ko','hi','id','de','fr','it','es','pt','ru'].indexOf(m[1]) === -1) return m[1];
    return 'home';
  }
  document.addEventListener('click', function (ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest('a[href]') : null;
    if (!a) return;
    var store = storeOf(a.getAttribute('href'));
    if (!store) return;
    if (typeof window.gtag === 'function') {
      window.gtag('event', 'store_click', {
        store: store,
        game: gameOf(a),
        page_lang: (document.documentElement.getAttribute('lang') || 'en')
      });
    }
  }, true);

  /* ---- 3. モバイルメニュー: 外側クリック / Esc で閉じる ---- */
  var burger = document.querySelector('.pr-burger');
  if (burger) {
    document.addEventListener('click', function (ev) {
      if (burger.open && !burger.contains(ev.target)) burger.open = false;
    });
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && burger.open) { burger.open = false; }
    });
  }

  /* ---- 4. 現在地をナビに反映 ------------------------------ */
  var path = location.pathname.replace(/\/(ja|zh|ko|hi|id|de|fr|it|es|pt|ru)\/$/, '/');
  var navLinks = document.querySelectorAll('.pr-header a[href]');
  for (var k = 0; k < navLinks.length; k++) {
    var href = navLinks[k].getAttribute('href') || '';
    if (href === '../' || href === '/' || href.indexOf('http') === 0) continue;
    var target = href.replace(/^\.\.\//, '/').replace(/^\.\//, '/');
    if (target !== '/' && path.indexOf(target) > -1) {
      navLinks[k].setAttribute('aria-current', 'page');
    }
  }

  /* ---- 5. 共通シェル（ヘッダー/フッター/Follow）の多言語化 ----
     各ページのインライン i18n 辞書はページ本文だけを担当し、シェルには触れない
     （19本のゲームページは辞書の書式が4通りで、機械挿入が危険なため分離した）。
     辞書 = assets/shell-i18n.js（正本 tools/shell_i18n.py の生成物）。
     言語の決定はページ側に任せ、ここは <html lang> の変化に追従するだけにする。
     こうするとページ側の実装形（setLang / applyLang の2系統）に依存しない。 */
  var SHELL = window.PR_SHELL_I18N;
  if (SHELL) {
    var applyShell = function (lang) {
      var dict = SHELL[lang] || SHELL.en;
      if (!dict) return;
      var els = document.querySelectorAll('[data-pr-i18n]');
      for (var n = 0; n < els.length; n++) {
        var el = els[n], key = el.getAttribute('data-pr-i18n');
        if (!(key in dict)) continue;
        var attr = el.getAttribute('data-pr-i18n-attr');
        if (attr) el.setAttribute(attr, dict[key]);
        else el.textContent = dict[key];
      }
    };
    var current = function () { return document.documentElement.getAttribute('lang') || 'en'; };
    applyShell(current());
    if (window.MutationObserver) {
      new MutationObserver(function () { applyShell(current()); })
        .observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
    }
  }

  /* ---- 5b. ダーク / ライトの切替 ----
     既定は墨ダーク（ブランドの意匠）。ライトは利用者が選んだときだけで、選択は保存される。
     復元は <head> の同期インラインが済ませているので、ここは切替とボタンの状態だけ担当する
     （復元まで defer のこのファイルに任せると、一瞬ダークが描かれてから明地に変わる）。 */
  var THEME_KEY = 'pixelryu_theme';
  var themeBtns = document.querySelectorAll('.pr-theme');
  if (themeBtns.length) {
    var syncBtns = function (theme) {
      for (var b = 0; b < themeBtns.length; b++) {
        themeBtns[b].setAttribute('aria-pressed', theme === 'light' ? 'true' : 'false');
      }
    };
    var setTheme = function (theme, persist) {
      if (theme === 'light') document.documentElement.setAttribute('data-theme', 'light');
      else document.documentElement.removeAttribute('data-theme');
      if (persist) { try { localStorage.setItem(THEME_KEY, theme); } catch (e) {} }
      /* ブラウザの UI（アドレスバー等）の色も地に合わせる。 */
      var mt = document.querySelector('meta[name="theme-color"]');
      if (mt) mt.setAttribute('content', theme === 'light' ? '#F4F1EA' : '#0B0E13');
      syncBtns(theme);
    };
    syncBtns(document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark');
    for (var tb = 0; tb < themeBtns.length; tb++) {
      themeBtns[tb].addEventListener('click', function () {
        var now = document.documentElement.getAttribute('data-theme') === 'light';
        setTheme(now ? 'dark' : 'light', true);
      });
    }
    /* 別タブで切り替えたら、こちらにも反映する。 */
    window.addEventListener('storage', function (ev) {
      if (ev.key === THEME_KEY && (ev.newValue === 'light' || ev.newValue === 'dark')) {
        setTheme(ev.newValue, false);
      }
    });
  }

  /* ---- 6. フッターの言語リンク: 選んだ言語を保存してから遷移 ----
     保存しないと、飛んだ先の言語ページで「前に保存された言語」が優先されて
     元の言語に戻ってしまう（localStorage → PAGE_LANG → navigator の優先順）。
     キーはページ側の LANG_STORAGE_KEY と同一でなければならない。 */
  document.addEventListener('click', function (ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest('a[data-pr-lang]') : null;
    if (!a) return;
    try { localStorage.setItem('pixelryu_lang_v2', a.getAttribute('data-pr-lang')); } catch (e) {}
  }, true);
})();
