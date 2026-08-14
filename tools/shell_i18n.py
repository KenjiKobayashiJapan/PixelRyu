#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
shell_i18n.py — 共通シェル（グローバルヘッダー / フッター / Follow 節）の12言語辞書。
**ここが唯一の正本**。2箇所から参照される:

  * tools/apply_shell.py   … assets/shell-i18n.js を生成（実行時の言語切替に使う）
  * tools/gen_i18n_pages.py … 言語ミラーへ静的に焼き込む（AIクローラは JS 非実行なので必須）

各ページのインライン i18n 辞書には足さない。19本のゲームページは辞書の書式が4通り
（うち3本は完全ミニファイ）で、そこへ機械挿入するのは危険なため。シェルは
`data-pr-i18n` 属性で完全に分離し、ページ側の i18n とは干渉しない。

語彙はトップページの既存訳から流用して統一している（新規に訳し直していない）:
  blurb 1文目=hero_title / h_games,nav_games=games_heading / h_follow=follow_heading
  e_roblox=roblox_t_more / news_cta=devlog_more
"""

# キー一覧（英語＝正）
#   skip      : スキップリンク
#   nav_*     : ヘッダーのナビ
#   aria_*    : スクリーンリーダー用ラベル（属性 aria-label に入る）
#   blurb     : フッター左のブランド説明
#   news_*    : フッターのニュースレター誘導
#   h_*       : フッターの見出し
#   e_*       : フッター Explore 列のリンク
#   contact   : フッター最下段
#   news_url  : 開発日誌の行き先。**日本語だけ note.com**（英語圏は Substack）。
#               日本語の読者には note が一次媒体なので、言語に応じてリンク先ごと切り替える。
SHELL = {
    "en": {
        "skip": "Skip to content",
        "nav_games": "Games", "nav_about": "About", "nav_press": "Press",
        "nav_news": "News", "nav_langs": "Languages",
        "aria_home": "PixelRyu home", "aria_menu": "Menu", "aria_lang": "Choose language",
        "aria_theme": "Switch between dark and light", "nav_theme": "Theme",
        "news_url": "https://pixelryu.substack.com/",
        "blurb": "Small games, crafted in Japan. Free on iPhone, Android and Roblox — in 12 languages.",
        "news_p": "Get new releases by email. It reaches you no matter what happens to any platform.",
        "news_cta": "Read the devlog",
        "h_explore": "Explore", "h_games": "Games", "h_langs": "Languages", "h_follow": "Follow",
        "e_games": "All games", "e_roblox": "Play on Roblox", "e_about": "About Ryu",
        "e_press": "Press kit", "e_support": "Support",
        "contact": "Contact",
    },
    "ja": {
        "skip": "本文へスキップ",
        "nav_games": "ゲーム", "nav_about": "開発者", "nav_press": "プレス",
        "nav_news": "開発日誌", "nav_langs": "言語",
        "aria_home": "PixelRyu ホーム", "aria_menu": "メニュー", "aria_lang": "言語を選ぶ",
        "aria_theme": "ダーク/ライトを切り替える", "nav_theme": "テーマ",
        "news_url": "https://note.com/pixelryu",
        "blurb": "小さなゲームを、日本から。iPhone・Android・Roblox で無料、12言語対応。",
        "news_p": "新作をメールでお届けします。プラットフォームに何があっても、あなたに届きます。",
        "news_cta": "開発日誌を読む",
        "h_explore": "サイト内", "h_games": "ゲーム", "h_langs": "言語", "h_follow": "フォロー",
        "e_games": "ゲーム一覧", "e_roblox": "Roblox で遊ぶ", "e_about": "Ryu について",
        "e_press": "プレスキット", "e_support": "サポート",
        "contact": "お問い合わせ",
    },
    "zh": {
        "skip": "跳到主要内容",
        "nav_games": "游戏", "nav_about": "关于", "nav_press": "媒体",
        "nav_news": "开发日志", "nav_langs": "语言",
        "aria_home": "PixelRyu 首页", "aria_menu": "菜单", "aria_lang": "选择语言",
        "aria_theme": "切换深色/浅色", "nav_theme": "主题",
        "news_url": "https://pixelryu.substack.com/",
        "blurb": "小小的游戏，来自日本。在 iPhone、Android 和 Roblox 上免费畅玩，支持 12 种语言。",
        "news_p": "通过邮件获取新作消息。无论平台发生什么，它都能送到你手中。",
        "news_cta": "阅读开发日志",
        "h_explore": "浏览", "h_games": "游戏", "h_langs": "语言", "h_follow": "关注",
        "e_games": "全部游戏", "e_roblox": "在 Roblox 上游玩", "e_about": "关于 Ryu",
        "e_press": "媒体资料", "e_support": "支持",
        "contact": "联系",
    },
    "ko": {
        "skip": "본문으로 건너뛰기",
        "nav_games": "게임", "nav_about": "소개", "nav_press": "프레스",
        "nav_news": "개발 일지", "nav_langs": "언어",
        "aria_home": "PixelRyu 홈", "aria_menu": "메뉴", "aria_lang": "언어 선택",
        "aria_theme": "다크/라이트 전환", "nav_theme": "테마",
        "news_url": "https://pixelryu.substack.com/",
        "blurb": "작은 게임을, 일본에서. iPhone·Android·Roblox에서 무료, 12개 언어 지원.",
        "news_p": "새 게임 소식을 이메일로 받아보세요. 플랫폼에 무슨 일이 생겨도 당신에게 도착합니다.",
        "news_cta": "개발 일지 읽기",
        "h_explore": "둘러보기", "h_games": "게임", "h_langs": "언어", "h_follow": "팔로우",
        "e_games": "게임 전체", "e_roblox": "Roblox에서 플레이", "e_about": "Ryu 소개",
        "e_press": "프레스 킷", "e_support": "지원",
        "contact": "문의하기",
    },
    "hi": {
        "skip": "मुख्य सामग्री पर जाएँ",
        "nav_games": "गेम्स", "nav_about": "परिचय", "nav_press": "प्रेस",
        "nav_news": "डेवलॉग", "nav_langs": "भाषाएँ",
        "aria_home": "PixelRyu होम", "aria_menu": "मेन्यू", "aria_lang": "भाषा चुनें",
        "aria_theme": "डार्क/लाइट बदलें", "nav_theme": "थीम",
        "news_url": "https://pixelryu.substack.com/",
        "blurb": "छोटे गेम, जापान में बने। iPhone, Android और Roblox पर मुफ़्त — 12 भाषाओं में।",
        "news_p": "नए गेम की जानकारी ईमेल पर पाएँ। किसी भी प्लैटफ़ॉर्म पर कुछ भी हो, यह आप तक पहुँचती रहेगी।",
        "news_cta": "डेवलॉग पढ़ें",
        "h_explore": "एक्सप्लोर", "h_games": "गेम्स", "h_langs": "भाषाएँ", "h_follow": "फ़ॉलो करें",
        "e_games": "सभी गेम्स", "e_roblox": "Roblox पर खेलें", "e_about": "Ryu के बारे में",
        "e_press": "प्रेस किट", "e_support": "सहायता",
        "contact": "संपर्क",
    },
    "id": {
        "skip": "Lewati ke konten",
        "nav_games": "Game", "nav_about": "Tentang", "nav_press": "Pers",
        "nav_news": "Devlog", "nav_langs": "Bahasa",
        "aria_home": "Beranda PixelRyu", "aria_menu": "Menu", "aria_lang": "Pilih bahasa",
        "aria_theme": "Ganti tema gelap/terang", "nav_theme": "Tema",
        "news_url": "https://pixelryu.substack.com/",
        "blurb": "Game kecil, dibuat di Jepang. Gratis di iPhone, Android, dan Roblox — dalam 12 bahasa.",
        "news_p": "Dapatkan rilis terbaru lewat email. Tetap sampai ke kamu apa pun yang terjadi pada platform.",
        "news_cta": "Baca devlog",
        "h_explore": "Jelajahi", "h_games": "Game", "h_langs": "Bahasa", "h_follow": "Ikuti",
        "e_games": "Semua game", "e_roblox": "Main di Roblox", "e_about": "Tentang Ryu",
        "e_press": "Press kit", "e_support": "Dukungan",
        "contact": "Kontak",
    },
    "de": {
        "skip": "Zum Inhalt springen",
        "nav_games": "Spiele", "nav_about": "Über", "nav_press": "Presse",
        "nav_news": "Devlog", "nav_langs": "Sprachen",
        "aria_home": "PixelRyu Startseite", "aria_menu": "Menü", "aria_lang": "Sprache wählen",
        "aria_theme": "Zwischen Dunkel und Hell wechseln", "nav_theme": "Design",
        "news_url": "https://pixelryu.substack.com/",
        "blurb": "Kleine Spiele, gemacht in Japan. Kostenlos auf iPhone, Android und Roblox — in 12 Sprachen.",
        "news_p": "Neue Spiele per E-Mail. Sie erreichen dich, egal was mit einer Plattform passiert.",
        "news_cta": "Devlog lesen",
        "h_explore": "Entdecken", "h_games": "Spiele", "h_langs": "Sprachen", "h_follow": "Folgen",
        "e_games": "Alle Spiele", "e_roblox": "Auf Roblox spielen", "e_about": "Über Ryu",
        "e_press": "Pressekit", "e_support": "Support",
        "contact": "Kontakt",
    },
    "fr": {
        "skip": "Aller au contenu",
        "nav_games": "Jeux", "nav_about": "À propos", "nav_press": "Presse",
        "nav_news": "Journal", "nav_langs": "Langues",
        "aria_home": "Accueil PixelRyu", "aria_menu": "Menu", "aria_lang": "Choisir la langue",
        "aria_theme": "Basculer entre sombre et clair", "nav_theme": "Thème",
        "news_url": "https://pixelryu.substack.com/",
        "blurb": "De petits jeux, façonnés au Japon. Gratuits sur iPhone, Android et Roblox — en 12 langues.",
        "news_p": "Recevez les nouveautés par e-mail. Elles vous parviennent quoi qu'il arrive aux plateformes.",
        "news_cta": "Lire le journal",
        "h_explore": "Explorer", "h_games": "Jeux", "h_langs": "Langues", "h_follow": "Suivre",
        "e_games": "Tous les jeux", "e_roblox": "Jouer sur Roblox", "e_about": "À propos de Ryu",
        "e_press": "Kit presse", "e_support": "Assistance",
        "contact": "Contact",
    },
    "it": {
        "skip": "Vai al contenuto",
        "nav_games": "Giochi", "nav_about": "Chi sono", "nav_press": "Stampa",
        "nav_news": "Devlog", "nav_langs": "Lingue",
        "aria_home": "Home di PixelRyu", "aria_menu": "Menu", "aria_lang": "Scegli la lingua",
        "aria_theme": "Passa da scuro a chiaro", "nav_theme": "Tema",
        "news_url": "https://pixelryu.substack.com/",
        "blurb": "Piccoli giochi, creati in Giappone. Gratis su iPhone, Android e Roblox — in 12 lingue.",
        "news_p": "Ricevi le novità via e-mail. Ti raggiungono qualunque cosa accada alle piattaforme.",
        "news_cta": "Leggi il devlog",
        "h_explore": "Esplora", "h_games": "Giochi", "h_langs": "Lingue", "h_follow": "Segui",
        "e_games": "Tutti i giochi", "e_roblox": "Gioca su Roblox", "e_about": "Chi è Ryu",
        "e_press": "Kit stampa", "e_support": "Supporto",
        "contact": "Contatti",
    },
    "es": {
        "skip": "Saltar al contenido",
        "nav_games": "Juegos", "nav_about": "Acerca de", "nav_press": "Prensa",
        "nav_news": "Diario", "nav_langs": "Idiomas",
        "aria_home": "Inicio de PixelRyu", "aria_menu": "Menú", "aria_lang": "Elegir idioma",
        "aria_theme": "Cambiar entre oscuro y claro", "nav_theme": "Tema",
        "news_url": "https://pixelryu.substack.com/",
        "blurb": "Juegos pequeños, hechos en Japón. Gratis en iPhone, Android y Roblox — en 12 idiomas.",
        "news_p": "Recibe los lanzamientos por correo. Te llegan pase lo que pase con cualquier plataforma.",
        "news_cta": "Leer el diario",
        "h_explore": "Explorar", "h_games": "Juegos", "h_langs": "Idiomas", "h_follow": "Seguir",
        "e_games": "Todos los juegos", "e_roblox": "Jugar en Roblox", "e_about": "Sobre Ryu",
        "e_press": "Kit de prensa", "e_support": "Soporte",
        "contact": "Contacto",
    },
    "pt": {
        "skip": "Ir para o conteúdo",
        "nav_games": "Jogos", "nav_about": "Sobre", "nav_press": "Imprensa",
        "nav_news": "Diário", "nav_langs": "Idiomas",
        "aria_home": "Início do PixelRyu", "aria_menu": "Menu", "aria_lang": "Escolher idioma",
        "aria_theme": "Alternar entre escuro e claro", "nav_theme": "Tema",
        "news_url": "https://pixelryu.substack.com/",
        "blurb": "Jogos pequenos, feitos no Japão. Grátis no iPhone, Android e Roblox — em 12 idiomas.",
        "news_p": "Receba os lançamentos por e-mail. Eles chegam até você aconteça o que acontecer com as plataformas.",
        "news_cta": "Ler o diário",
        "h_explore": "Explorar", "h_games": "Jogos", "h_langs": "Idiomas", "h_follow": "Seguir",
        "e_games": "Todos os jogos", "e_roblox": "Jogar no Roblox", "e_about": "Sobre o Ryu",
        "e_press": "Kit de imprensa", "e_support": "Suporte",
        "contact": "Contato",
    },
    "ru": {
        "skip": "Перейти к содержимому",
        "nav_games": "Игры", "nav_about": "Об авторе", "nav_press": "Пресса",
        "nav_news": "Дневник", "nav_langs": "Языки",
        "aria_home": "Главная PixelRyu", "aria_menu": "Меню", "aria_lang": "Выбрать язык",
        "aria_theme": "Переключить тёмную/светлую тему", "nav_theme": "Тема",
        "news_url": "https://pixelryu.substack.com/",
        "blurb": "Маленькие игры, сделанные в Японии. Бесплатно на iPhone, Android и Roblox — на 12 языках.",
        "news_p": "Получайте новые релизы по почте. Они дойдут до вас, что бы ни случилось с платформами.",
        "news_cta": "Читать дневник",
        "h_explore": "Разделы", "h_games": "Игры", "h_langs": "Языки", "h_follow": "Подписаться",
        "e_games": "Все игры", "e_roblox": "Играть в Roblox", "e_about": "О Ryu",
        "e_press": "Пресс-кит", "e_support": "Поддержка",
        "contact": "Контакты",
    },
}

LANG_CODES = list(SHELL.keys())


def check():
    """全言語が同じキー集合を持つことを保証する（欠けたキーは英語のまま残り事故になる）。"""
    base = set(SHELL["en"])
    for code, d in SHELL.items():
        miss = base - set(d)
        extra = set(d) - base
        if miss or extra:
            raise SystemExit(
                "shell_i18n: %s のキーが en と不一致（不足=%s 余分=%s）" % (code, sorted(miss), sorted(extra)))
    return True


if __name__ == "__main__":
    check()
    print("shell_i18n: %d 言語 × %d キー OK" % (len(SHELL), len(SHELL["en"])))
