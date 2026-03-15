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
- `scripts/draft_fetch.py` - URL 取得、title/description/site name 抽出
- `scripts/draft_tagging.py` - 主タグ / 補助タグ / タイトル候補の推定
- `scripts/draft_builder.py` - draft Markdown の組み立てと fallback item 生成
- `scripts/build_rewrite_prompt.py` - 下書き Markdown から生成AI投入用の prompt 文を組み立てる
- `scripts/prepare_llm_episode.py` - URL 3本から draft と prompt をまとめて用意する。URL を省くと schedule 由来の source 候補を表示
- `scripts/prepare_llm_episode.sh` - 上記 Python スクリプトの薄い wrapper
- `scripts/build_episode.py` - 日別ビルド本体。schedule 解決・render/index/audio/validate を担当
- `scripts/build_episode.sh` - 上記 Python スクリプトの薄い wrapper
- `scripts/render_audio.py` - VOICEVOX helper を使った音声生成本体
- `scripts/render_audio.sh` - 上記 Python スクリプトの薄い wrapper
- `scripts/schedule_models.py` - schedule 解決結果の dataclass 定義
- `scripts/index_models.py` - index 生成用 summary/view model の dataclass 定義
- `scripts/episode_models.py` - episode header/item/document の dataclass 定義
- `scripts/validate_config.py` - theme / schedule 設定の静的検証
- `scripts/validate.py` - サイト生成物全体の Python バリデータ本体
- `scripts/validate.sh` - 上記 Python スクリプトの薄い wrapper
- `scripts/episode_models.py` - episode header / item / tag / document の dataclass 定義
- `scripts/validate_config.py` - themes / schedule 設定の構造チェック
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
- `scripts/build_episode.py` - 日別ビルド本体（HTML / 台本 / index / 音声 / validate）
- `scripts/build_episode.sh` - 上記 Python スクリプトの薄い wrapper
- `scripts/show_schedule.py` - 日付から曜日ルールを引いて、その日の theme / coverage / speaker / site theme を表示
- `scripts/render_ogp.py` - Pillow でトップ OGP と日別 OGP を生成
- `scripts/validate.sh` - config 検証、テンプレ置換漏れ、生成物欠落、空ファイル、導線ずれなどを確認
- `scripts/publish.sh` - `main` の公開物を `gh-pages` に反映するローカル用スクリプト

### Themes / Templates / Site

- `config/themes/ai.json` - AIニュース用の既定テーマ設定
- `config/themes/default.json` - 後方互換用エイリアス設定
- `config/themes/shogi.json` - 将棋ニュース向けテーマ例
- `config/themes/vocaloid.json` - ボーカロイドニュース向けテーマ例
- `config/themes/sports.json` - スポーツニュース向けテーマ例
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
python3 scripts/draft_from_urls.py --theme ai --stdout 2026-03-13 \
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
また、下書きは `### Tags` を優先して出力し、各テーマ設定の `tag_rules` から自動タグ候補を添えます。
最終的な `headline / summary / script / tags` の自然な言い換えは生成AIで仕上げる前提です。

`draft_from_urls.py` は主に次を集めます。

- 記事タイトル（媒体名ノイズをできるだけ除去）
- 説明文候補（長すぎる文を短く整形）
- 媒体名
- 主タグの仮推定
- タグベースの episode タイトル案
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
- `## Theme` (`ai` / `shogi` / `vocaloid` / `sports` など)
- `## Coverage` (`daily` / `weekly`)
- `## Window` (`YYYY-MM-DD..YYYY-MM-DD`)
- `## Summary`
- `## Intro`
- `## Script Intro`
- `## Item 1` 〜 `## Item 3`
  - `### Headline`
  - `### Summary`
  - `### Tags` （任意、複数可）
  - `### Category` （旧形式。未移行回との互換用）
  - `### Source`
  - `### Script` （空欄なら Summary から仮生成）
- `## Script Closing`
- `## Closing`

`### Source` は次のように 1 行で書けます。

```md
### Source
[媒体名](https://example.com/article)
```

`## Theme` は必須で、`config/themes/<name>.json` に対応する theme 名を指定します。現在は `ai` / `shogi` / `vocaloid` / `sports` を使えます。
`## Coverage` は `daily` / `weekly`、`## Window` は対象期間を `YYYY-MM-DD..YYYY-MM-DD` で書きます。
`render_episode.py` はこれらの値を自動で読んで、適切なテーマと期間表示で日別ページと OGP を生成します。

設計上は **site theme** と **episode theme** を分けています。
トップページ (`index.html`) のブランドや OGP は site theme で決め、各回の表示ラベルや日別ページは episode 本文の `## Theme` を真実源として扱います。

`### Tags` は自由記述です。複数行でも 1 行カンマ区切りでも書けます。

```md
### Tags
製品
初音ミク
歌声合成
```

旧形式の `### Category` も引き続き読めますが、新規作成では `### Tags` を推奨します。

`### Tags` と `### Category` の両方を省略した場合は、当面 theme ごとの既定タグを使います。

## Rendering and Publishing

### 1. 日次ビルドを一発で回す

```bash
./scripts/build_episode.sh 2026-03-13
```

話者を変えたい場合:

```bash
./scripts/build_episode.sh 2026-03-13 zundamon
# または schedule を使う
./scripts/build_episode.sh 2026-03-13
```

内部では次を順に実行します。

- `python3 scripts/render_episode.py 2026-03-13`
- `python3 scripts/update_index.py` （site theme ベースでトップを再構築）

公開日はファイル名の日付を使い、実際のニュース対象期間は `## Window` で持ちます。特定テーマを曜日ごとに回す場合も、この構成なら「公開日」と「直近1週間の対象期間」を分けて運用できます。
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
python3 scripts/render_ogp.py --theme ai --date 2026-03-13 --title "AI規制・研究・半導体"
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
./scripts/new_episode.sh --theme ai 2026-03-13 "AI規制・研究・半導体"
```

トップページの絞り込みは、細かいタグではなく **episode の `Theme` (`ai` / `shogi` / `vocaloid` / `sports`)** を軸にします。
`Tags` は各回・各項目の文脈を補う自由ラベルとして扱います。
なおトップカード上のタグ表示は、**1カード内で重複除去した一覧表示** にしています。
最新回は featured と recent の両方に表示し、featured は大きい見せ方、recent は一覧として扱います。

## Schedule

曜日ごとの運用ルールは `config/schedule.json` で持ちます。

例:

```json
{
  "defaults": {
    "speaker": "zundamon",
    "site_theme": "ai",
    "coverage": "weekly"
  },
  "weekday_rules": {
    "saturday": { "theme": "vocaloid", "coverage": "weekly" },
    "sunday": { "theme": "shogi", "coverage": "weekly" }
  }
}
```

確認コマンド:

```bash
python3 scripts/show_schedule.py 2026-03-14
python3 scripts/show_schedule.py --json 2026-03-14
```

`build_episode.sh` を **speaker 省略** で呼ぶと、その日の schedule から speaker / site theme を拾います。
`new_episode.py` / `draft_from_urls.py` も、theme / coverage / window を省略すると schedule を参照します。
`prepare_llm_episode.sh YYYY-MM-DD` のように URL なしで呼ぶと、その日の source 候補一覧を表示します。

## Recommended Minimal Flow

普段の最短手順はこれです。

```bash
./scripts/prepare_llm_episode.sh 2026-03-13
# ↑ その日の schedule と source 候補を確認

./scripts/prepare_llm_episode.sh 2026-03-13 \
  "https://example.com/a" \
  "https://example.com/b" \
  "https://example.com/c"

# prompts/generated/2026-03-13.ai.prompt.txt を生成AIへ投入
# 生成AIの出力を episodes/2026-03-13.md に保存
./scripts/build_episode.sh 2026-03-13
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
