# 最初にクローリングするとき

1. organization 内に設定ファイルを作る
   1. sample を参考に作る
   2. organization/<クローリング名>/ROD/LIST/SETTING.txt
   3. organization/<クローリング名>/ROD/LIST/START_LIST.txt
   4. organization/<クローリング名>/ROD/LIST/DOMAIN.json
2. STARTLIST.json に探索開始URLを入力
3. 探索可能ドメインを DOMAIN.json の allow の中に入力
4. クローリングをかける `python src/main.py <クローリング名>`
5. 新しいサーバが見つかった場合 <クローリング名>/new_link_filter.json ができているのでその中からクローリングしたいURLを DOMAIN.json のなかに追加
