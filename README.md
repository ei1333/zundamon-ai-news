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
- 1つの episode ソースから HTML と台本を生成する構成に変更済み

## Files on `main`

- `index.html` - トップページ
- `episodes/_template.md` - エピソード原稿のテンプレ
- `episodes/YYYY-MM-DD.md` - 日々の入力元になる原稿
- `days/YYYY-MM-DD.html` - episode 原稿から生成される公開ページ
- `scripts_text/YYYY-MM-DD.txt` - episode 原稿から生成される読み上げ台本
- `assets/audio/` - 音声ファイル配置場所
- `assets/style.css` - 共通スタイル
- `scripts/new_episode.sh` - 新しい原稿ファイルを作り、初回レンダリングと index 更新を行うスクリプト
- `scripts/render_episode.py` - episode 原稿から HTML と台本テキストを生成するスクリプト
- `scripts/render_audio.sh` - 生成済み台本テキストから音声を生成するスクリプト
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

これで次の変更が入ります。

- `episodes/2026-03-13.md` をテンプレから生成
- `days/2026-03-13.html` を初回レンダリング
- `scripts_text/2026-03-13.txt` を初回レンダリング
- `index.html` の最新回リンクを更新
- `index.html` のバックナンバー先頭に新規回を追加

### 3. 原稿を埋める

`episodes/YYYY-MM-DD.md` は、見出しベースの書きやすい書式です。

- `# タイトル`
- `## Summary`
- `## Intro`
- `## Item 1` 〜 `## Item 3`
  - `### Headline`
  - `### Summary`
  - `### Source` （`[媒体名](URL)` で書ける）
  - `### Script`
- `## Script Closing`
- `## Closing`

つまり、`key: value` を並べるより普通の Markdown に近い感覚で書けるようにしています。

特に `### Source` は次のように 1 行で書けます。

```md
### Source
[媒体名](https://example.com/article)
```

### 4. HTML と台本を再生成する

原稿を編集したら、HTML と台本を再生成します。

```bash
./scripts/render_episode.py 2026-03-13
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
- 日別ページ本文
- 音声ファイルの配置

必要ならローカルでも公開前チェックを実行できます。

```bash
./scripts/validate.sh
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

## Notes

- `gh-pages` 側には `README.md` やテンプレファイルを出さない
- `gh-pages` 側には `episodes/` や `scripts_text/` を出さない
- GitHub Pages の公開元は `gh-pages` branch に切り替える前提
- 環境依存の絶対パスは README に固定で書かない
- GitHub Actions に `contents: write` 権限が必要
- `main` への push 後、Actions タブで publish workflow の成功を確認できる

## Next Ideas

- episode 原稿の書式をもっと書きやすくする
- 出典URLからHTML断片を生成
- 公開前チェックをさらに増やす
- index のバックナンバー更新をさらに自動化
- ニュース番組っぽい UI に寄せる
