# zundamon-ai-news

ずんだもん音声で毎日のAIニュースを1分前後にまとめて届ける、静的サイト用リポジトリです。

## Overview

このリポジトリでは、1つの episode 原稿から次を生成します。

- 日別ページ `days/YYYY-MM-DD.html`
- 読み上げ台本 `scripts_text/YYYY-MM-DD.txt`
- 日別 OGP 画像 `assets/ogp-YYYY-MM-DD.png`
- トップページ `index.html` に載せる最新回・最近の回・バックナンバー導線

公開は GitHub Pages 前提で、`main` で編集し `gh-pages` に公開物だけを反映します。

## Current Workflow

現在の基本方針は次です。

1. URL 3本から下書きを作る
2. LLM で `headline / summary / script` を整える
3. episode 原稿をレンダリングして公開する

つまり、`draft_from_urls.py` は **素材収集と下書き生成**、
LLM は **自然な編集**、
`render_episode.py` 以降は **公開物生成** を担当します。

## Main Files

### Editorial / Drafting

- `scripts/draft_from_urls.py` - 記事 URL 3本から episode 原稿の下書きを生成
- `scripts/build_rewrite_prompt.py` - 下書き Markdown から生成AI投入用の prompt 文を組み立てる
- `scripts/prepare_llm_episode.sh` - URL 3本から draft と prompt をまとめて用意する
- `prompts/episode_rewrite_prompt.txt` - 機械が読む prompt テンプレート本体
- `prompts/episode_rewrite_prompt.md` - prompt の説明と運用メモ
- `examples/shogi_rewrite_example.md` - 将棋ニュース下書き → 生成AI整形の最小サンプル

### Episode Sources / Outputs

- `episodes/YYYY-MM-DD.md` - 入力元になる原稿
- `days/YYYY-MM-DD.html` - 原稿から生成される公開ページ
- `scripts_text/YYYY-MM-DD.txt` - 原稿から生成される読み上げ台本
- `assets/audio/` - 音声ファイル配置場所
- `assets/ogp-YYYY-MM-DD.png` - 日別ページ用 OGP 画像

### Rendering / Publishing

- `scripts/render_episode.py` - 原稿から HTML / 台本 / 日別 OGP を生成
- `scripts/update_index.py` - episode 一覧から `index.html` を再構築
- `scripts/render_audio.sh` - 生成済み台本テキストから音声を生成
- `scripts/build_episode.sh` - 日別ビルドを一発で回す（HTML / 台本 / index / 音声 / validate）
- `scripts/render_ogp.py` - Pillow でトップ OGP と日別 OGP を生成
- `scripts/validate.sh` - テンプレ置換漏れ、生成物欠落、空ファイル、導線ずれなどを確認
- `scripts/publish.sh` - `main` の公開物を `gh-pages` に反映するローカル用スクリプト

### Themes / Templates / Site

- `config/themes/default.json` - 既定テーマ設定
- `config/themes/shogi.json` - 将棋ニュース向けテーマ例
- `config/theme.json` - 互換用の既定テーマ参照
- `scripts/templates/` - 日別ページ / トップページ / partial 類のテンプレート群
- `index.html` - トップページ
- `assets/style.css` - 共通スタイル
- `assets/ogp.svg` - OGP デザインの元 SVG
- `assets/ogp.png` - トップページ用 OGP 画像
- `.github/workflows/publish.yml` - `main` への push を公開反映する GitHub Actions

## Setup

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

## LLM Workflow

### 1. URL から下書きを作る

```bash
python3 scripts/draft_from_urls.py --theme default --stdout 2026-03-13 \
  "https://example.com/a" \
  "https://example.com/b" \
  "https://example.com/c"
```

将棋テーマ例:

```bash
python3 scripts/draft_from_urls.py --theme shogi --stdout 2026-03-13 \
  "https://www.shogi.or.jp/match_news/2026/03/260312_t_result_01.html" \
  "https://www.shogi.or.jp/news/2026/03/260308_n_result_01.html" \
  "https://www.shogi.or.jp/match_news/2026/03/260313_t_01.html"
```

この段階では、見出し整形は保守的にとどめます。
最終的な `headline / summary / script` の自然な言い換えは生成AIで仕上げる前提です。

`draft_from_urls.py` は主に次を集めます。

- 記事タイトル（媒体名ノイズをできるだけ除去）
- 説明文候補（長すぎる文を短く整形）
- 媒体名
- カテゴリ仮推定
- カテゴリベースの episode タイトル案
- URL 取得失敗時の slug ベース簡易フォールバック

### 2. LLM 用 prompt を組み立てる

最短では次の一発準備スクリプトが使えます。

```bash
./scripts/prepare_llm_episode.sh --theme shogi 2026-03-13 \
  "https://www.shogi.or.jp/match_news/2026/03/260312_t_result_01.html" \
  "https://www.shogi.or.jp/news/2026/03/260308_n_result_01.html" \
  "https://www.shogi.or.jp/match_news/2026/03/260313_t_01.html"
```

このスクリプトは次を作ります。

- `drafts/YYYY-MM-DD.<theme>.draft.md`
- `prompts/generated/YYYY-MM-DD.<theme>.prompt.txt`

手でつなぐ場合は、従来どおり次でも作れます。

```bash
python3 scripts/draft_from_urls.py --theme shogi --stdout 2026-03-13 \
  "https://www.shogi.or.jp/match_news/2026/03/260312_t_result_01.html" \
  "https://www.shogi.or.jp/news/2026/03/260308_n_result_01.html" \
  "https://www.shogi.or.jp/match_news/2026/03/260313_t_01.html" \
| python3 scripts/build_rewrite_prompt.py 2026-03-13 --theme shogi
```

補助ファイル:

- `prompts/episode_rewrite_prompt.txt`
- `prompts/episode_rewrite_prompt.md`
- `examples/shogi_rewrite_example.md`

### 3. LLM で原稿を整える

生成AIには次を任せます。

- 短く自然な `Headline`
- 簡潔な `Summary`
- 読み上げ向きの `Script`

特に `Script` では、表示の美しさより読み上げやすさを優先します。
将棋テーマでは `叡王戦` → `えいおうせん` のように、難しい語をひらがなへ開く方針です。

返ってきた Markdown を `episodes/YYYY-MM-DD.md` に保存します。

## Episode Format

`episodes/YYYY-MM-DD.md` は Markdown 見出しベースです。

- `# タイトル`
- `## Summary`
- `## Intro`
- `## Script Intro`
- `## Item 1` 〜 `## Item 3`
  - `### Headline`
  - `### Summary`
  - `### Category` （任意）
  - `### Source`
  - `### Script` （空欄なら Summary から仮生成）
- `## Script Closing`
- `## Closing`

`### Source` は次のように 1 行で書けます。

```md
### Source
[媒体名](https://example.com/article)
```

`### Category` を省略した場合は、当面次の既定値を使います。

- 1本目 → `透明性`
- 2本目 → `研究`
- 3本目 → `インフラ`

## Rendering and Publishing

### 1. 日次ビルドを一発で回す

```bash
./scripts/build_episode.sh 2026-03-13
```

話者を変えたい場合:

```bash
./scripts/build_episode.sh 2026-03-13 zundamon
```

内部では次を順に実行します。

- `python3 scripts/render_episode.py 2026-03-13`
- `python3 scripts/update_index.py`
- `./scripts/render_audio.sh 2026-03-13 zundamon`
- `./scripts/validate.sh`

### 2. 個別に再生成する

```bash
python3 scripts/render_episode.py 2026-03-13
python3 scripts/update_index.py
./scripts/render_audio.sh 2026-03-13 zundamon
```

`render_audio.sh` の既定出力先は `assets/audio/sample-news-YYYY-MM-DD.wav` です。

`### Script` が空欄の項目は、`### Headline` と `### Summary` を使って仮の読み上げ文を自動生成します。

### 3. OGP を個別に再生成する

トップページ用 OGP:

```bash
python3 scripts/render_ogp.py
```

日別ページ用 OGP:

```bash
python3 scripts/render_ogp.py --theme default --date 2026-03-13 --title "AI規制・研究・半導体"
```

### 4. 公開前チェック

```bash
./scripts/validate.sh
```

主な確認内容:

- 未置換テンプレマーカーやプレースホルダの残り
- episode 原稿が正しくパースできること
- 各回の HTML / 台本 / 音声 / OGP の存在と非空
- `index.html` が最新回を含み、各日別ページへ導線を持つこと
- 日別ページの audio / OGP / OGP メタ情報の整合
- OGP で詰まりやすい長すぎタイトルやトピック過多の warning

### 5. main に保存して公開する

```bash
git add .
git commit -m "Add daily AI news for 2026-03-13"
git push origin main
```

通常は `main` への push で GitHub Actions が `gh-pages` を更新します。
ローカルで手動反映する場合のみ次を使います。

```bash
./scripts/publish.sh
```

## Optional: Start from a Blank Episode

URL ベースではなく、空の原稿から始めたい場合は次を使えます。

```bash
./scripts/new_episode.sh --theme default 2026-03-13 "AI規制・研究・半導体"
```

## Recommended Minimal Flow

普段の最短手順はこれです。

```bash
./scripts/prepare_llm_episode.sh 2026-03-13 \
  "https://example.com/a" \
  "https://example.com/b" \
  "https://example.com/c"

# prompts/generated/2026-03-13.default.prompt.txt を生成AIへ投入
# 生成AIの出力を episodes/2026-03-13.md に保存
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

## Next Ideas

- LLM 整形フローの追加自動化
- 公開前チェックの拡充
- 音声生成と公開確認の運用安定化
- ニュース番組っぽい UI / 演出の強化
