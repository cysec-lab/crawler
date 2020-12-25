# ブラックリスト

クローラにはURLにブラックリストのワードが入っている場合にはクローリングしない機能がある

## リスト入りを果たしたURL

- `www.ritsumei.ac.jp/ocw/`
  - 内部で使っている <wj.ax.xrea.com> というアクセス解析サービス? が終了しており一生読み込まれ続ける
  - タイムアウトでHTMLは取得できるがタイムロスにつながるのでブラックリスト入りを果たした

## 時間短縮用BL

- `~hirai`
  - `www.ritsumei.ac.jp/se/~hirai/`, `www.ritsumei.ac.jp/~hirai/`
  - ひたすらページとかソースコードが多いため削除
  - matlabのコードとかがめちゃ置いてある
  - 3100ページ程度
- `www.ritsumei.ac.jp/acd/gr`
  - 文系大学院のサイトがいろいろまとまっていそう
  - 1000ページ程度
- `www.ritsumei.ac.jp/acd/re/`
  - 総合科学技術研究機構のサイト
  - 1500ページ程度
- `www.ritsumei.ac.jp/research/`
  - 研究所系のサイトをまとめて
  - 研究、産学官連携系サイトたち
  - 2,400ページ程度
- `www.ritsumei.ac.jp/ir/isaru/`
  - 立命館大学国際関係学会
  - 1200ページ程度
- `www.ritsumei.ac.jp/se/re/izumilab/`
  - 動的再構成システム研究室
  - 全然更新されているが授業ページなどかなりあるので削除
  - 900ページ程度
- `www.ritsumei.ac.jp/lifescience/`
  - 生命科学の研究室のサイトたち
  - 700ページ程度
- `www.ritsumei.ac.jp/primary/`
  - 小学校消した
  - 500ページ程度
- `www.ritsumei.ac.jp/mng/gl/koho`, `www.ritsumei.ac.jp/rs`
  - 過去の広報ページ
  - いまは features のページに移動した
  - 1100 + 867 = 2000ページ程度


18589