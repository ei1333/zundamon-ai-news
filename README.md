# zundamon-ai-news

ずんだもん音声で短いAIニュースを届ける静的サイトの試作リポジトリです。

## Status

- GitHub Pages での公開確認用プロトタイプ
- 2026-03-12 の実ニュース入りサンプルを公開済み
- VOICEVOX を使ったローカル音声生成フローを確認済み

## Files

- `index.html` - トップページ
- `days/2026-03-12.html` - 現在の公開サンプル
- `days/_template.html` - 次回以降のページ作成テンプレ
- `assets/audio/` - 音声ファイル配置場所
- `assets/style.css` - 共通スタイル

## Daily Workflow

### 1. ニュースを3本選ぶ

バランスのよい3本にするとまとまりやすいです。

- ルール / 透明性
- 安全性 / 実利用
- 半導体 / インフラ / 市場

### 2. 日別ページを作る

テンプレートをコピーして日付を差し替えます。

```bash
cd /home/ei1333hobby/zundamon-ai-news
cp days/_template.html days/2026-03-13.html
```

置換する主な項目:

- `YYYY-MM-DD`
- 音声ファイル名
- 見出し3本
- 要約本文
- 出典リンク

### 3. 読み上げ台本を作る

目安:

- 1分前後
- 3本構成
- 最後にひとことまとめ

### 4. VOICEVOX で音声を生成する

VOICEVOX helper:

- Script: `/home/ei1333hobby/.openclaw/workspace/voicevox_tts.sh`
- Docs: `/home/ei1333hobby/.openclaw/workspace/docs/voicevox.md`

例:

```bash
mkdir -p assets/audio
/home/ei1333hobby/.openclaw/workspace/voicevox_tts.sh \
  zundamon \
  "こんにちはなのだ。ずんだもん一分エーアイニュース、三月十三日版なのだ。" \
  assets/audio/sample-news-2026-03-13.wav
```

### 5. トップページを更新する

- 最新回リンク
- バックナンバー一覧

### 6. 公開する

```bash
git add .
git commit -m "Add daily AI news for 2026-03-13"
git push
```

## Next Ideas

- 日別ページ生成をスクリプト化
- 台本テンプレを別ファイル化
- 出典URLからHTML断片を生成
- index のバックナンバー更新を自動化
