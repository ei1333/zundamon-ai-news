# episode_rewrite_prompt

公開用の episode 原稿へ整形するための LLM プロンプト説明です。

## Files

- `prompts/episode_rewrite_prompt.txt`
  - 機械が読む実テンプレート
- `prompts/episode_rewrite_prompt.md`
  - 人向けの説明と運用メモ

## Purpose

- `scripts/draft_from_urls.py` が集めた素材をベースにする
- 最終的な `headline` / `summary` / `script` を生成AIで自然に整える
- ルールベースで例外処理を増やしすぎない

## Recommended Input

生成AIには次をまとめて渡します。

1. 編集方針
2. 出力フォーマット指定
3. 素材（3本分の title / description / source / category）

通常は `scripts/build_rewrite_prompt.py` が `.txt` テンプレートに素材を流し込み、生成AIへ渡す最終 prompt 文を組み立てます。

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
2. `build_rewrite_prompt.py` で prompt 文を組み立てる
3. その prompt を生成AIへ渡す
4. 返ってきた Markdown を `episodes/YYYY-MM-DD.md` に保存する
5. `render_episode.py` → `update_index.py` → `render_audio.sh` の順に実行する

## Future Direction

必要なら将来的に次も追加できます。

- theme ごとのプロンプト分岐
- JSON 出力モード
- `headline` / `summary` / `script` だけを返す部分整形モード
- CLI から LLM を呼ぶ自動整形ステップ
