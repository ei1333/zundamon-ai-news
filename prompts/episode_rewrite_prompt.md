# episode_rewrite_prompt.md

URL から集めた下書きを、公開用の episode 原稿へ整形するためのプロンプト雛形です。

## Purpose

- `scripts/draft_from_urls.py` が集めた素材をベースにする
- 最終的な `headline` / `summary` / `script` を生成AIで自然に整える
- ルールベースで例外処理を増やしすぎない

## Recommended Input

生成AIには、次の3層をまとめて渡す想定です。

1. **編集方針**
2. **出力フォーマット指定**
3. **素材（3本分の title / description / source / category）**

## Prompt Template

```text
あなたはニュース編集者です。
以下の素材をもとに、日本語の短い音声ニュース原稿を作成してください。

要件:
- 3本構成にする
- 読み上げ時間は全体で1分前後を想定する
- 見出しは短く、意味が一目で分かる自然な日本語にする
- summary は各項目 1〜2文で簡潔にする
- script は実際に読み上げやすい自然文にする
- source の事実から逸脱しない
- 不明な点は断定せず、素材にある情報だけでまとめる
- 元の title にある媒体名ノイズや過剰に長い対局カード表現は、必要に応じて自然に言い換える
- 将棋テーマでは「挑戦権獲得」「第5局で勝利」など、意味が明快な表現を優先する

出力形式:
次の Markdown 構造を厳密に守ってください。

# {episode_title}

## Summary
...

## Intro
...

## Script Intro
...

## Item 1
### Headline
...

### Summary
...

### Category
...

### Source
[媒体名](URL)

### Script
...

## Item 2
### Headline
...

### Summary
...

### Category
...

### Source
[媒体名](URL)

### Script
...

## Item 3
### Headline
...

### Summary
...

### Category
...

### Source
[媒体名](URL)

### Script
...

## Script Closing
...

## Closing
...

素材:
- テーマ: {theme_name}
- 日付: {date}
- 下書き:
{draft_markdown}
```

## Example Notes

### AI ニュース向け

- 見出しは「OpenAI が新機能を公開」「xAI が新モデルを発表」くらいの短さを目安
- Summary は背景を詰め込みすぎず、何が起きたかを優先

### 将棋ニュース向け

- 見出しは「叡王戦 斎藤慎太郎八段が挑戦権」「王将戦第5局 藤井王将が勝利」くらいを目安
- 対局カードをそのまま長く読むより、結果が伝わる形を優先
- 女流棋戦も同様に、勝者と結果を先に置く

## Minimal Operator Flow

1. `draft_from_urls.py --stdout` で下書きを作る
2. その出力をこのプロンプトに差し込んで生成AIへ渡す
3. 返ってきた Markdown を `episodes/YYYY-MM-DD.md` に保存する
4. `render_episode.py` → `update_index.py` → `render_audio.sh` の順に実行する

## Future Direction

必要なら将来的に次も追加できます。

- theme ごとのプロンプト分岐
- JSON 出力モード
- `headline` / `summary` / `script` だけを返す部分整形モード
- CLI から LLM を呼ぶ自動整形ステップ
