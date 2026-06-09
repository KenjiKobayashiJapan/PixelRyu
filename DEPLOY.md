# PixelRyu サイト デプロイ手順（チェックリスト）

> このディレクトリ（`PixelRyu/`）自体が公開リポ `pixelryu.github.io` の git リポジトリ。
> `git push origin main` すると GitHub Pages が再ビルドして本番反映される。
>
> **このリストの目的: 「パンくずリストが消える」事故を含む、デプロイ時の取りこぼしを無くす。**

---

## 0. デプロイ前チェック（必須・1コマンド）

```bash
python3 tools/check_site.py
```

- **ERROR が出たら直すまで push しない。**
- 特に `[breadcrumb] ... NOT in breadcrumb.js APP_NAMES` は
  「新アプリを `breadcrumb.js` に登録し忘れ → そのページのパンくずが無言で消える」を検出する。
- `WARN` は参考（任意対応）。`ERROR` のみがブロック条件。

---

## A. パンくずリストを消さないためのルール（最重要・今回の事故の原因）

パンくずは共有スクリプト **`breadcrumb.js`** が URL からアプリを判定して描画する。
`breadcrumb.js` の `detect()` は、URL のディレクトリ名（slug）が `APP_NAMES` に
**無いと `null` を返し、パンくずを一切描画しない**（エラーも出ない＝無言で消える）。

新しいアプリのページを追加・公開するときは必ず:

- [ ] サブページ（`<app>/*.html`）に
      `<script src="../breadcrumb.js?v=YYYYMMDDHHMMSS" defer></script>` が入っている
- [ ] **`breadcrumb.js` の `APP_NAMES` にその slug（＝ディレクトリ名）を登録**してある
      例: `"tatami":      { all: "TATAMI" }`（和名ブランドが別なら `ja:` も付ける）
- [ ] `<head>` に `BreadcrumbList` の JSON-LD が入っている
- [ ] **`breadcrumb.js` を編集したら、影響ページの `?v=` を新タイムスタンプに更新する**
      - 理由: `?v=` は複数ページで**同じ値を共有**していることがある。古いままだと、
        別ページで旧 `breadcrumb.js` を**キャッシュ済み**の訪問者が、同じ `?v=` の新ページでも
        旧スクリプト（新アプリ未対応）を使ってしまい、パンくずが出ない。
      - 最低限、**追加・変更したアプリの全ページ**（index / overview / privacy / terms）を更新する。

> ⚠️ 今回の事故: TATAMI 追加時に `APP_NAMES` へ `tatami` を登録し忘れ、4ページ全部でパンくず消滅。
> 対策として上記を `tools/check_site.py` が機械チェックする。

---

## B. 動画・画像を差し替えたとき（キャッシュバスティング）

- [ ] ソース（各アプリ `NN_<app>/store/...`）→ `PixelRyu/<app>/` にコピー
- [ ] `md5 <src> <dst>` でソースとコピーの**ハッシュ一致**を確認
- [ ] 参照の `?v=` を**全箇所**新タイムスタンプに更新
      - 例: TEMARI 横長動画は **3箇所**（`<source>` ＋ JS の `ja`/`en` 言語別差し替え）
- [ ] タイムスタンプは `date +%Y%m%d%H%M%S` で取得（年月日時分秒・各2桁）
- [ ] 動画は**無加工で反映**（ユーザー制作の原本を再圧縮・上書きしない）

---

## C. コミット & プッシュ

- [ ] `python3 tools/check_site.py` が `OK`
- [ ] `git add -A <変更ファイル>` → `git status --short` で**意図通りの差分のみ**か確認
- [ ] コミットメッセージは日本語 `[種別] 要約（50字以内）` ＋ 箇条書き ＋ 末尾に
      `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- [ ] 大容量（動画）push 対策はこのリポに設定済み:
      `git config http.version HTTP/1.1` / `git config http.postBuffer 524288000`
- [ ] `git push origin main`。`408` が出たら**まず同じコマンドでリトライ**（断続的に起きる）
- [ ] push 後: `git status` がクリーン、かつ
      `git rev-list --left-right --count origin/main...HEAD` が `0	0`

---

## 付録: 現在 `breadcrumb.js` に登録済みのアプリ slug

`mole-whack` / `liquid-glow` / `hotaru` / `issen` / `parcel-pals` / `sumlings` /
`hayate` / `bounce-cat` / `temari` / `tatami`

新アプリを足したらここと `breadcrumb.js` の `APP_NAMES` の両方を更新する。
