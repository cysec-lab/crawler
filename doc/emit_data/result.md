# resultに作られるもの

- [resultに作られるもの](#resultに作られるもの)
  - [js関連の結果](#js関連の結果)
    - [js_only_exist_in_request.csv](#js_only_exist_in_requestcsv)
    - [js_only_exist_in_html.csv](#js_only_exist_in_htmlcsv)
    - [js_new.csv](#js_newcsv)
    - [js_hash_same.csv](#js_hash_samecsv)
    - [js_hash_change.csv](#js_hash_changecsv)
    - [js_obf_<normal, random. encode>.csv](#js_obf_normal-random-encodecsv)
    - [js_obftree_<normal, random. encode>.csv](#js_obftree_normal-random-encodecsv)
  - [page関連の結果](#page関連の結果)
    - [page_script_in_title.csv](#page_script_in_titlecsv)
    - [page_strange_script_name.csv](#page_strange_script_namecsv)
    - [page_meta_refresh.csv](#page_meta_refreshcsv)
    - [page_invisible_iframe.csv](#page_invisible_iframecsv)
    - [page_diff_of_frequent_words.csv](#page_diff_of_frequent_wordscsv)
    - [page_diff_of_important_word.csv](#page_diff_of_important_wordcsv)
    - [page_hack_word_LvX.txt](#page_hack_word_lvxtxt)
    - [page_changed_html.csv](#page_changed_htmlcsv)
    - [page_sshash_change.csv](#page_sshash_changecsv)
    - [page_new.csv](#page_newcsv)
    - [page_hash_same.csv](#page_hash_samecsv)
    - [page_hash_change.csv](#page_hash_changecsv)
    - [page_after_redirect.csv](#page_after_redirectcsv)
  - [ファイル関連の結果](#ファイル関連の結果)
    - [file_new.csv](#file_newcsv)
    - [file_hash_same.csv](#file_hash_samecsv)
    - [file_hash_change.csv](#file_hash_changecsv)
    - [file_different_size.csv](#file_different_sizecsv)
  - [URLに関して](#urlに関して)
    - [url_access_denied_by_robots.csv](#url_access_denied_by_robotscsv)
  - [エラー関連](#エラー関連)
    - [error_failed_to_get_window_url.txt](#error_failed_to_get_window_urltxt)
    - [error_clamd.txt](#error_clamdtxt)
  - [その他](#その他)
    - [server](#server)
    - [result.txt](#resulttxt)
    - [notice.txt](#noticetxt)

## js関連の結果

### js_only_exist_in_request.csv

拡張機能で取得したリクエストの中にあってHTMLの中には書かれていない`<script src=""`
クエリは除いて考えている

### js_only_exist_in_html.csv

HTMLの中には書かれているのに拡張機能で取得したリクエストの中には存在していないscriptのリクエスト `<script src=""`
クエリは除いて考えている

### js_new.csv

新規JSが発見された場合に記録される

### js_hash_same.csv

JSのhashが変化しなかった場合に記録される

### js_hash_change.csv

JSのハッシュ値が変化した場合に記録される

### js_obf_<normal, random. encode>.csv

既存研究(難読化の特徴を利用したドライブバイダウンロード攻撃検知についての検討)で実装されたJSの難読化検証決定木を用いた難読化判定を行う。

- normal
  - 通常のコード
- random
  - ランダム難読化が施されたコード
- encode
  - エンコード難読化が施されている

### js_obftree_<normal, random. encode>.csv

独自に作成した決定木を用いてJSの難読化検知を行った結果が格納される

- normal
  - 通常のコード
- random
  - ランダム難読化が施されたコード
- encode
  - エンコード難読化が施されている


## page関連の結果

### page_script_in_title.csv

タイトルの中に `script` 等の文字が含まれている怪しい系
`dealwebpage/script_analyze.py/script_inspection()` で呼び出される `title_inspection()` で判断される

### page_strange_script_name.csv

- スクリプト名が怪しいものたちがまとめられる
- スクリプト名が1文字のとき、怪しいスクリプト名のときに記録する
- `dealwebpage/script_analyze.py/script_inspection()` で呼び出される `script_name_inspection()` で判断される

### page_meta_refresh.csv

`<meta http-equiv="refresh` に類似する(`Refresh`, `rEfresh`)リダイレクトのコードが存在する場合に記録される
`dealwebpage/script_analyze.py/meta_refresh_inspection()` で調べる

### page_invisible_iframe.csv

- 目に見えないiframeが存在する場合に記録
- `<iframe>` はHTML のインラインフレーム要素であり, 入れ子になった閲覧コンテキストを表現する
- width、height属性値が0か display:none か visibility:hidden が設定されている等、目に見えない `<iframe>` が記録される
- `dealwebpage/script_analyze.py/iframe_inspection()` で検査される

### page_diff_of_frequent_words.csv

このサーバの頻出単語リストと調べているページの頻出単語リストを比較した結果を記録

### page_diff_of_important_word.csv

このサーバでの重要単語と調べているページの重要語リストを比較した結果を記録

### page_hack_word_LvX.txt

Hackワードとして指定した文字列が見つかったサイトを記録

### page_changed_html.csv

SETTING.txt にて `html_diff=True` にすると実行される検査
page内のHTMLを記録しておきどこが変化したかが記録される.

### page_sshash_change.csv

sshashが変化したページが記録される

### page_new.csv

- 新規にできたページが記録される
- `crawler.py/parse()` で作成
- url_dict に存在しないページの場合これは新規ページ

### page_hash_same.csv

- ハッシュ値が過去のものと一致するサイトが記録される
- `crawler.py/parse()` で作成
- url_dict に存在するSHAと新たに取得したSHAが一致するかを調べて作成

### page_hash_change.csv

- ハッシュ値の変化したページが記録される
- `crawler.py/parse()` で作成
- Hash値が変わったページに関して何日で変わったかを記録する

### page_after_redirect.csv

リダイレクトした際にリダイレクトもととリダイレクト後のURLが保存される

## ファイル関連の結果

### file_new.csv

- 新規ファイルが記録される
- url_dict に存在しないページの場合これは新規ファイル

### file_hash_same.csv

ハッシュ値が変化しなかったファイルが記録される

### file_hash_change.csv

ハッシュ値が変化したファイルが記録される

### file_different_size.csv

サイズが変化したファイルが記録される

## URLに関して

### url_access_denied_by_robots.csv

robots.txt に検査を阻まれたURLたちが記録されていく

## エラー関連

### error_failed_to_get_window_url.txt

別窓やタブが開いた際にURLを取るのに失敗したら記録される
どんなときに発生するのかよくわからん

### error_clamd.txt

Clamdで発生したエラーがまとめられている

## その他

### server

各サーバの検査結果が記録されている

### result.txt

達成URL数を全部まとめて記録する

### notice.txt

特殊なケースとしてなんかKillされた時等に記録されるページ
