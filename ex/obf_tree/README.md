# 難読化検知決定木作成

難読化されたJSデータを検知するための決定木を作成するためのブランチ

ここで作られた pkl ファイルを用いて難読化検知を行う。

## src

- collector
  - リストに書かれているJSを取ってきて保存する
- encoder
  - 難読化処理を行うスクリプトたち
- data_creator
  - JSファイルからそれぞれの特徴を元にCSVをつくる
- investigator
  - 実際にpklを作るためのnotebook
