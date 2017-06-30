# crawler

mecabのインストール、path通しは必須。
clamd、phantomjsはインストールしていない場合、ROD/LIST/SETTING.txtで使用しないように設定可能。
機械学習もしない場合は設定でしないようにできる。

インストールする必要があるライブラリ(標準ライブラリではない)
BeautifulSoup4 ： スクレイピングに使う
mecab-python ： mecabを使ったスクレイピングに使う

任意(なくても動く)
lxml ： html.parserの代わり。beautifulsoupで使う。(処理が速い)
selenium ： phantomJSを使うため
pyClamd ： clamAVのclamdを使うため
scikit-learn ： 機械学習ライブラリ
numpy(mklつき?) : 機械学習ライブラリ
