# shogi_rewrite_example.md

`prompts/episode_rewrite_prompt.md` を使って、将棋ニュース下書きを生成AIで整えるときの最小サンプルです。

## Example Input Draft

```md
# タイトル戦・藤井聡太王将VS永瀬拓矢九段 ALSOK杯第75期王将戦七番勝負第5局 藤井王将の勝利・大島綾華女流二段VS磯谷祐維女流初段 第37期女流王位戦挑戦者決定戦

## Summary
2026-03-13 の回では、永瀬拓矢九段VS斎藤慎太郎八段 第11期叡王戦挑戦者決定戦 斎藤八段の勝利、藤井聡太王将VS永瀬拓矢九段 ALSOK杯第75期王将戦七番勝負第5局 藤井王将の勝利、大島綾華女流二段VS磯谷祐維女流初段 第37期女流王位戦挑戦者決定戦の3本を掲載しています。

## Intro
2026-03-13 時点の公開情報をもとに構成した、今週の将棋ニュース下書きです。内容を確認して整えてください。

## Script Intro
今週の将棋ニュース3本なのだ。

## Item 1
### Headline
永瀬拓矢九段VS斎藤慎太郎八段 第11期叡王戦挑戦者決定戦 斎藤八段の勝利

### Summary
日本将棋連盟の永瀬拓矢九段VS斎藤慎太郎八段 第11期叡王戦挑戦者決定戦 斎藤八段の勝利のページです。

### Category
タイトル戦

### Source
[shogi.or.jp](https://www.shogi.or.jp/match_news/2026/03/260312_t_result_01.html)

### Script

## Item 2
### Headline
藤井聡太王将VS永瀬拓矢九段 ALSOK杯第75期王将戦七番勝負第5局 藤井王将の勝利

### Summary
日本将棋連盟の藤井聡太王将VS永瀬拓矢九段 ALSOK杯第75期王将戦七番勝負第5局 藤井王将の勝利のページです。

### Category
タイトル戦

### Source
[shogi.or.jp](https://www.shogi.or.jp/news/2026/03/260308_n_result_01.html)

### Script

## Item 3
### Headline
大島綾華女流二段VS磯谷祐維女流初段 第37期女流王位戦挑戦者決定戦

### Summary
日本将棋連盟の大島綾華女流二段VS磯谷祐維女流初段 第37期女流王位戦挑戦者決定戦のページです。

### Category
女流棋戦

### Source
[shogi.or.jp](https://www.shogi.or.jp/match_news/2026/03/260313_t_01.html)

### Script

## Script Closing
以上、今週の将棋ニュースまとめなのだ。

## Closing
※ この記事は公開情報をもとにした短い要約です。詳細は各出典をご確認ください。
```

## Example Output Image

生成AIには、上の素材から次のような方向で整形してほしいです。

- Item 1 headline → `叡王戦 斎藤慎太郎八段が挑戦権`
- Item 2 headline → `王将戦第5局 藤井王将が勝利`
- Item 3 headline → `女流王位戦 大島綾華女流二段が挑戦権`

## Example Output Snippet

```md
## Item 1
### Headline
叡王戦 斎藤慎太郎八段が挑戦権

### Summary
第11期叡王戦の挑戦者決定戦で斎藤慎太郎八段が勝ち、タイトル挑戦権を獲得しました。

### Script
まず1本目なのだ。叡王戦の挑戦者決定戦で、斎藤慎太郎八段が勝って挑戦権を手にしたのだ。
```

## Intended Use

1. `draft_from_urls.py --stdout` の結果を用意する
2. `prompts/episode_rewrite_prompt.md` のテンプレに貼る
3. この example のような粒度で、headline / summary / script を短く自然に整える
