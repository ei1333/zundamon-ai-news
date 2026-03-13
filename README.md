# zundamon-ai-news

ずんだもん音声で毎日のAIニュースを1分前後にまとめて届ける、静的サイト用リポジトリです。

## Overview

このリポジトリでは、1つのエピソード原稿から次を生成します。

- 日別ページ `days/YYYY-MM-DD.html`
- 読み上げ台本 `scripts_text/YYYY-MM-DD.txt`
- 日別OGP画像 `assets/ogp-YYYY-MM-DD.png`
- トップページ `index.html` に載せる最新回・最近の回・バックナンバー導線

公開は GitHub Pages を前提にしており、`main` で編集して `gh-pages` に公開物だけを反映する運用です。

## Branch Structure

- `main`
  - 原稿
  - スクリプト
  - テンプレート
  - README
  - 生成物の管理元
- `gh-pages`
  - GitHub Pages に載せる公開用静的ファイルのみ

## Current Status

- GitHub Pages で日次AIニュースサイトとして運用中
- 2026-03-10 以降の回を公開済み
- `main` への push で GitHub Actions から公開反映する構成
- 1つの episode 原稿から HTML / 台本 / 日別 OGP を生成する構成
- `scripts/update_index.py` でトップページの最新回・最近の回・説明文・バックナンバーを再構築可能
- VOICEVOX を使ったローカル音声生成フローを確認済み

## Requirements

- Python 3
- `requirements.txt` にある依存関係
- VOICEVOX を使う場合はローカルの音声生成環境

セットアップ例:

```bash
cd /path/to/zundamon-ai-news
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Main Files

- `index.html` - トップページ
- `episodes/_template.md` - 旧テンプレート参考用（新規作成は theme 設定から生成）
- `episodes/YYYY-MM-DD.md` - 日々の入力元になる原稿
- `days/YYYY-MM-DD.html` - 原稿から生成される公開ページ
- `scripts_text/YYYY-MM-DD.txt` - 原稿から生成される読み上げ台本
- `assets/audio/` - 音声ファイル配置場所
- `assets/style.css` - 共通スタイル
- `assets/ogp.svg` - OGP デザインの元 SVG
- `assets/ogp.png` - トップページ用 OGP 画像
- `assets/ogp-YYYY-MM-DD.png` - 日別ページ用 OGP 画像
- `scripts/new_episode.sh` - `new_episode.py` を呼ぶ薄いラッパー
- `scripts/new_episode.py` - 新しい原稿ファイル作成 + 初回レンダリング（`--no-index` 対応）
- `config/themes/default.json` - 既定テーマ設定（canonical）
- `config/theme.json` - 互換用の既定テーマ参照（将来的に廃止予定）
- `scripts/draft_from_urls.py` - 記事URL 3本から episode 原稿の下書きを生成
- `scripts/render_episode.py` - 原稿から HTML / 台本 / 日別 OGP を生成
- `scripts/update_index.py` - episode 一覧から `index.html` を再構築
- `scripts/render_audio.sh` - 生成済み台本テキストから音声を生成
- `scripts/build_episode.sh` - 日別ビルドを一発で回す（HTML / 台本 / index / 音声 / validate）
- `scripts/render_ogp.py` - Pillow でトップ OGP と日別 OGP を生成
- `scripts/validate.sh` - テンプレ置換漏れ、生成物欠落、空ファイル、最新回導線ずれ、HTML 参照崩れなどを確認
- `scripts/publish.sh` - `main` の公開物を `gh-pages` に反映するローカル用スクリプト
- `scripts/templates/` - 日別ページ / トップページ / partial 類のテンプレート群
- `.github/workflows/publish.yml` - `main` への push を公開反映する GitHub Actions

## Daily Workflow

### 1. ニュースを3本選ぶ

1回1分前後に収めるなら、3本構成が扱いやすいです。

例:

- ルール / 透明性
- 研究 / 安全性 / 実利用
- 半導体 / インフラ / 市場

### 2. 新しい episode を作る

まずは新しい日付の原稿ひな形を作ります。新規作成時の既定文言は theme 設定から生成されます。

```bash
cd /path/to/zundamon-ai-news
./scripts/new_episode.sh 2026-03-13 "AI規制・研究・半導体"
```

`index.html` の更新を後回しにしたい場合は `--no-index` も使えます。

```bash
./scripts/new_episode.sh --no-index 2026-03-13 "AI規制・研究・半導体"
```

将来のテーマ切替を見据えて、theme 名も指定できます。

```bash
./scripts/new_episode.sh --theme default 2026-03-13 "AI規制・研究・半導体"
```

これで主に次が作られます。

- `episodes/2026-03-13.md`
- `days/2026-03-13.html`
- `scripts_text/2026-03-13.txt`
- 必要に応じて `index.html` の最新回・バックナンバー導線

### 3. URL から下書きを作る（任意）

出典URLが先にある場合は、3本まとめて原稿下書きを作れます。

```bash
python3 scripts/draft_from_urls.py --theme default 2026-03-13 \
  "https://example.com/a" \
  "https://example.com/b" \
  "https://example.com/c"
```

既存ファイルを上書きしたくないので、`episodes/YYYY-MM-DD.md` がすでにある場合は停止します。

まず内容を標準出力だけで見たい場合は `--stdout` も使えます。

```bash
python3 scripts/draft_from_urls.py --theme default --stdout 2026-03-13 \
  "https://example.com/a" \
  "https://example.com/b" \
  "https://example.com/c"
```

このスクリプトは各URLから次を拾って下書き化します。

- 記事タイトル（媒体名ノイズをできるだけ除去し、見出し表記も少し整形）
- 説明文候補（長すぎる文を短く整形）
- 媒体名
- カテゴリ仮推定
- カテゴリベースの episode タイトル案
- URL取得失敗時の slug ベース簡易フォールバック

### 4. 原稿を埋める

`episodes/YYYY-MM-DD.md` は Markdown 見出しベースです。

- `# タイトル`
- `## Summary`
- `## Intro`
- `## Item 1` 〜 `## Item 3`
  - `### Headline`
  - `### Summary`
  - `### Category` （任意）
  - `### Source`
  - `### Script` （空欄なら Summary から仮生成）
- `## Script Closing`
- `## Closing`

`### Category` を省略した場合は、当面次の既定値を使います。

- 1本目 → `透明性`
- 2本目 → `研究`
- 3本目 → `インフラ`

`### Source` は次のように1行で書けます。

```md
### Source
[媒体名](https://example.com/article)
```

### 5. 日次ビルドを一発で回す

普段はまずこのコマンドを使うのが最短です。

```bash
./scripts/build_episode.sh 2026-03-13
```

話者を変えたい場合:

```bash
./scripts/build_episode.sh 2026-03-13 zundamon
```

このコマンドは内部で次を順に実行します。

- `python3 scripts/render_episode.py 2026-03-13`
- `python3 scripts/update_index.py`
- `./scripts/render_audio.sh 2026-03-13 zundamon`
- `./scripts/validate.sh`

### 6. HTML / 台本 / 日別 OGP を個別に再生成する

原稿を編集したあとに個別確認したい場合は、従来どおり単体実行もできます。

```bash
python3 scripts/render_episode.py 2026-03-13
```

このコマンドで次が再生成されます。

- `days/2026-03-13.html`
- `scripts_text/2026-03-13.txt`
- `assets/ogp-2026-03-13.png`

`### Script` が空欄の項目は、`### Headline` と `### Summary` を使って仮の読み上げ文を自動生成します。

### 7. トップページを再構築する

トップページの最新回表示・最近の回・説明文・バックナンバーを更新したい場合は次を実行します。

```bash
python3 scripts/update_index.py
```

### 8. VOICEVOX で音声を生成する

VOICEVOX helper は環境に合わせて指定します。

例:

- `VOICEVOX_TTS_SCRIPT=~/path/to/voicevox_tts.sh`
- `VOICEVOX_TTS_SCRIPT=${VOICEVOX_TTS_SCRIPT:-$HOME/.openclaw/workspace/voicevox_tts.sh}`

実行例:

```bash
cd /path/to/zundamon-ai-news
VOICEVOX_TTS_SCRIPT="${VOICEVOX_TTS_SCRIPT:-$HOME/.openclaw/workspace/voicevox_tts.sh}"
./scripts/render_audio.sh 2026-03-13
```

必要なら話者名も指定できます。

```bash
./scripts/render_audio.sh 2026-03-13 zundamon
```

### 9. 確認する

最低限、次を確認します。

- トップページの最新回リンク
- バックナンバー一覧
- 日別ページ本文
- Category 表示
- 音声ファイルの配置
- OGP 画像の見た目

公開前チェック:

```bash
./scripts/validate.sh
```

現在の `validate.sh` では主に次を確認します。

- 未置換テンプレマーカーやプレースホルダの残り
- episode 原稿が正しくパースできること
- 各回の HTML / 台本 / 音声 / OGP の存在と非空
- `index.html` が最新回を含み、各日別ページへ導線を持つこと
- 日別ページの audio / OGP / OGP メタ情報の整合
- OGP で詰まりやすい長すぎタイトルやトピック過多の warning

### 10. OGP を個別に再生成する

トップページ用 OGP:

```bash
python3 scripts/render_ogp.py
```

テーマを明示したい場合:

```bash
python3 scripts/render_ogp.py --theme default
```

日別ページ用 OGP:

```bash
python3 scripts/render_ogp.py --theme default --date 2026-03-13 --title "AI規制・研究・半導体"
```

日別 OGP のタイトルは `・` ごとのトピック単位で2行に分配し、収まりきらない場合は末尾トピックごと省略します。

### 11. `main` に保存する

```bash
git add .
git commit -m "Add daily AI news for 2026-03-13"
git push origin main
```

### 12. 公開する

通常は `main` に push すれば GitHub Actions が `gh-pages` を更新します。

```bash
git push origin main
```

ローカルで手動反映する場合のみ、補助的に次を使います。

```bash
./scripts/publish.sh
```

## Recommended Minimal Flow

普段の最短手順はこれです。

```bash
./scripts/new_episode.sh 2026-03-13 "AI規制・研究・半導体"
./scripts/build_episode.sh 2026-03-13 zundamon
git add .
git commit -m "Add daily AI news for 2026-03-13"
git push origin main
```

## Credits

- 音声: VOICEVOX:ずんだもん

## Notes

- `gh-pages` 側には `README.md` やテンプレファイルを出さない
- `gh-pages` 側には `episodes/` や `scripts_text/` を出さない
- GitHub Pages の公開元は `gh-pages` branch を想定
- 環境依存の絶対パスは固定で書かない
- GitHub Actions には `contents: write` 権限が必要
- `main` への push 後、Actions タブで publish workflow の成功を確認できる

## Next Ideas

- 出典 URL から下書き情報を取り込みやすくする
- 公開前チェックをさらに増やす
- 音声生成と公開確認の運用をさらに安定化する
- ニュース番組っぽい UI / 演出を強化する
- エピソード作成フローをさらに省力化する
