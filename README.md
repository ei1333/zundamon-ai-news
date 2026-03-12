# zundamon-ai-news

ずんだもん音声で短いAIニュースを届ける静的サイトの試作リポジトリです。

## Branch Structure

- `main` - 作業用ブランチ
  - テンプレ
  - README
  - scripts
  - 将来の自動化用ファイル
- `gh-pages` - 公開用ブランチ
  - GitHub Pages に載せる静的ファイルだけを置く

## Status

- GitHub Pages での公開確認用プロトタイプ
- 2026-03-12 の実ニュース入りサンプルを公開済み
- VOICEVOX を使ったローカル音声生成フローを確認済み
- `gh-pages` を公開専用ブランチとして作成済み
- `main` への push で GitHub Actions が公開反映する構成に変更済み

## Files on `main`

- `index.html` - トップページ
- `days/2026-03-12.html` - 現在の公開サンプル
- `days/_template.html` - 日別HTMLページのテンプレ
- `scripts_text/_template.txt` - 読み上げ台本のテンプレ
- `assets/audio/` - 音声ファイル配置場所
- `assets/style.css` - 共通スタイル
- `scripts/new_episode.sh` - 新しい日付ページ・台本・index導線を作るスクリプト
- `scripts/render_audio.sh` - 台本テキストから音声を生成するスクリプト
- `scripts/publish.sh` - `main` の公開物を `gh-pages` へ反映するローカル用スクリプト
- `.github/workflows/publish.yml` - `main` への push を `gh-pages` 公開へ反映する GitHub Actions

## Daily Workflow

### 1. ニュースを3本選ぶ

バランスのよい3本にするとまとまりやすいです。

- ルール / 透明性
- 安全性 / 実利用
- 半導体 / インフラ / 市場

### 2. 日別ページと台本を作る

生成スクリプトで日付ページ、台本、index の導線を作ります。

```bash
cd /path/to/zundamon-ai-news
./scripts/new_episode.sh 2026-03-13 "AI規制・研究・半導体"
```

これで次の変更が入ります。

- `days/2026-03-13.html` をテンプレから生成
- `scripts_text/2026-03-13.txt` を台本テンプレから生成
- `index.html` の最新回リンクを更新
- `index.html` のバックナンバー先頭に新規回を追加

そのあと手で埋める主な項目:

- HTML側の見出し3本
- HTML側の要約本文
- 出典リンク
- 台本テキスト
- 必要に応じてトップ文言

### 3. 読み上げ台本を整える

目安:

- 1分前後
- 3本構成
- 最後にひとことまとめ

台本は `scripts_text/YYYY-MM-DD.txt` に保存します。

### 4. VOICEVOX で音声を生成する

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

### 5. 内容を確認する

- トップページの最新回リンク
- バックナンバー一覧
- 日別ページ本文
- 音声ファイルの配置

### 6. `main` に保存する

```bash
git add .
git commit -m "Add daily AI news for 2026-03-13"
git push origin main
```

### 7. 公開する

基本は `main` に push すると GitHub Actions が自動で `gh-pages` を更新します。

```bash
git push origin main
```

ローカルで手動反映したい場合は、補助的に次も使えます。

```bash
./scripts/publish.sh
```

## Notes

- `gh-pages` 側には `README.md` や `days/_template.html` を出さない
- `gh-pages` 側には `scripts_text/` も出さない
- GitHub Pages の公開元は `gh-pages` branch に切り替える前提
- 環境依存の絶対パスは README に固定で書かない
- GitHub Actions に `contents: write` 権限が必要
- `main` への push 後、Actions タブで publish workflow の成功を確認できる

## Next Ideas

- HTML と台本の情報源を1つに寄せる
- 出典URLからHTML断片を生成
- 公開前チェックを Actions に追加
- index のバックナンバー更新をさらに自動化
- ニュース番組っぽい UI に寄せる
