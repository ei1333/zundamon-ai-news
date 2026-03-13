# zundamon-ai-news

ずんだもん音声で短いAIニュースを届ける静的サイトのリポジトリです。

## Branch Structure

- `main` - 作業用ブランチ
  - テンプレ
  - README
  - scripts
  - 将来の自動化用ファイル
- `gh-pages` - 公開用ブランチ
  - GitHub Pages に載せる静的ファイルだけを置く

## Status

- GitHub Pages で公開する日次AIニュースサイトとして運用中
- 2026-03-10 以降の回を公開済み
- VOICEVOX を使ったローカル音声生成フローを確認済み
- `gh-pages` を公開専用ブランチとして運用
- `main` への push で GitHub Actions が公開反映する構成
- 1つの episode ソースから HTML と台本を生成する構成
- `scripts/update_index.py` でトップページの最新回表示・最近の回・説明文・バックナンバーを再構築可能

## Files on `main`

- `index.html` - トップページ
- `episodes/_template.md` - エピソード原稿のテンプレ
- `episodes/YYYY-MM-DD.md` - 日々の入力元になる原稿
- `days/YYYY-MM-DD.html` - episode 原稿から生成される公開ページ
- `scripts_text/YYYY-MM-DD.txt` - episode 原稿から生成される読み上げ台本
- `assets/audio/` - 音声ファイル配置場所
- `assets/style.css` - 共通スタイル
- `assets/ogp.svg` - OGPデザインの元SVG
- `assets/ogp.png` - トップページ用OGP画像
- `assets/ogp-YYYY-MM-DD.png` - 日別ページ用OGP画像
- `scripts/new_episode.sh` - `new_episode.py` を呼ぶ薄いラッパー
- `scripts/new_episode.py` - 新しい原稿ファイルを安全に作り、初回レンダリングを行うスクリプト（`--no-index` 対応）
- `scripts/render_episode.py` - episode 原稿から HTML と台本テキストを生成するスクリプト
- `scripts/update_index.py` - episode 一覧から index を全生成するスクリプト
- `scripts/templates/day.html` - 日別ページ用テンプレート
- `scripts/templates/index.html` - トップページ用テンプレート
- `scripts/templates/index_featured.html` - トップの最新回セクション用テンプレート
- `scripts/templates/index_recent_card.html` - 最近の回カード用テンプレート
- `scripts/templates/index_backnumber_item.html` - バックナンバー項目用テンプレート
- `scripts/templates/partial_tag.html` - タグ表示用の共通 partial
- `scripts/templates/partial_headline_item.html` - 見出しリスト項目用の共通 partial
- `scripts/render_audio.sh` - 生成済み台本テキストから音声を生成するスクリプト
- `scripts/render_ogp.py` - Pillowで共通OGP画像と日別OGP画像を生成するスクリプト
- `scripts/validate.sh` - 公開前にテンプレ置換漏れや音声参照切れを確認するスクリプト
- `scripts/publish.sh` - `main` の公開物を `gh-pages` へ反映するローカル用スクリプト
- `.github/workflows/publish.yml` - `main` への push を `gh-pages` 公開へ反映する GitHub Actions

## Daily Workflow

### 1. ニュースを3本選ぶ

バランスのよい3本にするとまとまりやすいです。

- ルール / 透明性
- 安全性 / 実利用
- 半導体 / インフラ / 市場

### 2. 原稿ファイルを作る

生成スクリプトで原稿、初回HTML、初回台本、index の導線を作ります。

```bash
cd /path/to/zundamon-ai-news
./scripts/new_episode.sh 2026-03-13 "AI規制・研究・半導体"
```

index 更新をあとでやりたいときは、次も使えるめう。

```bash
./scripts/new_episode.sh --no-index 2026-03-13 "AI規制・研究・半導体"
```

これで次の変更が入ります。

- `episodes/2026-03-13.md` をテンプレから生成
- `days/2026-03-13.html` を初回レンダリング
- `scripts_text/2026-03-13.txt` を初回レンダリング
- `index.html` の最新回リンクを更新
- `index.html` のバックナンバーを episode 一覧から再構築
- `index.html` のトップ説明文を episode の `## Summary` から更新

### 3. 原稿を埋める

`episodes/YYYY-MM-DD.md` は、見出しベースの書きやすい書式です。

- `# タイトル`
- `## Summary`
- `## Intro`
- `## Item 1` 〜 `## Item 3`
  - `### Headline`
  - `### Summary`
  - `### Category` （任意。例: `透明性` / `研究` / `インフラ` / `安全性` / `市場`）
  - `### Source` （`[媒体名](URL)` で書ける）
  - `### Script` （空でも可。空欄なら Summary から仮生成）
- `## Script Closing`
- `## Closing`

つまり、`key: value` を並べるより普通の Markdown に近い感覚で書けるようにしています。

`### Category` を省略した場合は、当面は 1本目=透明性 / 2本目=研究 / 3本目=インフラ の既定値を使います。

特に `### Source` は次のように 1 行で書けます。

```md
### Source
[媒体名](https://example.com/article)
```

### 4. HTML と台本を再生成する

原稿を編集したら、HTML と台本を再生成します。

`### Script` を空欄にした項目は、`### Headline` と `### Summary` を使って仮の読み上げ文を自動生成します。
このとき日別ページ用の `assets/ogp-YYYY-MM-DD.png` も同時生成されます。

```bash
./scripts/render_episode.py 2026-03-13
```

トップページの最新回表示・最新3回カード・説明文・バックナンバーを episode 一覧から再構築したいときは、これも使えます。

```bash
./scripts/update_index.py
```

### 5. VOICEVOX で音声を生成する

VOICEVOX helper は環境に合わせて指定します。

例:

- `VOICEVOX_TTS_SCRIPT=~/path/to/voicevox_tts.sh`
- もしくは `VOICEVOX_TTS_SCRIPT=${VOICEVOX_TTS_SCRIPT:-$HOME/.openclaw/workspace/voicevox_tts.sh}`

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

### 6. 内容を確認する

- トップページの最新回リンク
- バックナンバー一覧
- 日別ページ本文（Category 表示も含む）
- 音声ファイルの配置

必要ならローカルでも公開前チェックを実行できます。

```bash
./scripts/validate.sh
```

トップページ用OGP画像を再生成したいときはこれめう。

```bash
python3 scripts/render_ogp.py
```

日別ページ用OGP画像を個別に再生成したいときはこれめう。

```bash
python3 scripts/render_ogp.py --date 2026-03-13 --title "AI規制・研究・半導体" --summary "公開情報をもとに独自要約したAIニュース回"
```

### 7. `main` に保存する

```bash
git add .
git commit -m "Add daily AI news for 2026-03-13"
git push origin main
```

### 8. 公開する

基本は `main` に push すると GitHub Actions が自動で `gh-pages` を更新します。

```bash
git push origin main
```

ローカルで手動反映したい場合は、補助的に次も使えます。

```bash
./scripts/publish.sh
```

## Credits

- 音声: VOICEVOX:ずんだもん

## Notes

- `gh-pages` 側には `README.md` やテンプレファイルを出さない
- `gh-pages` 側には `episodes/` や `scripts_text/` を出さない
- GitHub Pages の公開元は `gh-pages` branch に切り替える前提
- 環境依存の絶対パスは README に固定で書かない
- GitHub Actions に `contents: write` 権限が必要
- `main` への push 後、Actions タブで publish workflow の成功を確認できる

## Next Ideas

- 出典URLから下書き情報を取り込みやすくする
- 公開前チェックをさらに増やす
- 音声生成と公開確認の運用をさらに安定化する
- ニュース番組っぽい UI / 演出を強化する
- エピソード作成フローをさらに省力化する
