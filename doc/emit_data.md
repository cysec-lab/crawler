# クローラから出力される結果たち

- [クローラから出力される結果たち](#クローラから出力される結果たち)
  - [alert で出力されるもの](#alert-で出力されるもの)
    - [request_to_new_server.csv](#request_to_new_servercsv)
    - [link_to_new_server.csv](#link_to_new_servercsv)
    - [after_redirect_check.csv](#after_redirect_checkcsv)
    - [new_form_url.csv](#new_form_urlcsv)
    - [new_iframeSrc.csv](#new_iframesrccsv)
    - [new_page_without_frequent_word.csv](#new_page_without_frequent_wordcsv)
    - [url_history](#url_history)
  - [organization の中に作成されるもの](#organization-の中に作成されるもの)
    - [new_request_filter.json](#new_request_filterjson)
    - [new_link_filter.json](#new_link_filterjson)
  - [resultに作られるもの](#resultに作られるもの)
    - [js_only_exist_in_request.csv](#js_only_exist_in_requestcsv)
    - [js_only_exist_in_html.csv](#js_only_exist_in_htmlcsv)
    - [js_new.csv](#js_newcsv)
    - [js_hash_same.csv](#js_hash_samecsv)
    - [js_hash_change.csv](#js_hash_changecsv)
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
    - [file_new.csv](#file_newcsv)
    - [file_hash_same.csv](#file_hash_samecsv)
    - [file_hash_change.csv](#file_hash_changecsv)
    - [file_different_size.csv](#file_different_sizecsv)
    - [url_access_denied_by_robots.csv](#url_access_denied_by_robotscsv)
    - [error_failed_to_get_window_url.txt](#error_failed_to_get_window_urltxt)
    - [error_clamd.txt](#error_clamdtxt)

## alert で出力されるもの

### request_to_new_server.csv

- crawler.extract_extension_data_and_inspection() で作成される
- 怪しいURLへのリクエストを行っていないかを調査
  - 各ページを調査してrequest先のURLを収集
  - `check_allow_url.inspection_url_by_filter()` でフィルタに当てはまったりするURLか調査
- 組織外(知らないホスト)のURLならば記録される
- Args
  - url_initial
    - 調査対象として送られてきたURL
  - url
    - 実際に調査したURL
  - link
    - ページに含まれている知らないホストへのリンクたち

### link_to_new_server.csv

- crawler.extract_extension_data_and_inspection() で作成される
- 知らないサーバへリンクしていないか調査
  - 各ページを調査してrequest先のURLを収集
  - `check_allow_url.inspection_url_by_filter()` でフィルタに当てはまったりするURLか調査
- 組織外(知らないホスト)のURLならば記録される
- Args
  - url_initial
    - 調査対象として送られてきたURL
  - url
    - 実際に調査したURL
  - link
    - ページに含まれている知らないホストへのリンクたち

### after_redirect_check.csv

TODO: 修正の必要あり

- リダイレクトが発生した際に記録される
- なんかいまはうまく動いていない
  - ファイルのDLチェックページが開いたときを記録してそう

### new_form_url.csv

TODO: 辞書作成の必要あり

- ホワイトリストにない入力formが存在した場合にactionにかかれているURLが記録される
- `crawler.parser()` で作成される
- 辞書がまだ作られていないので作ってもいいかもしれない

### new_iframeSrc.csv

- 新たに見つかった新規iframeが追記される
- `inspection_page.iframe_inspection()` で探す
  - iframe の src が別である際にはそのURLsetが返ってくる

### new_page_without_frequent_word.csv

TODO: 3回クロールしてどう変わるかでちょっと話が変わってくるのでしばらく待機

### url_history

urlの遷移が起きた場合に記録する、なんか怪しいものも記録されてるぞ....

## organization の中に作成されるもの

### new_request_filter.json

`alertdir` の中の `new_request_url.csv` をもとに `make_filter_from_past_data.make_filter()` で作られる.

### new_link_filter.json

`alertdir` の中の `link_to_new_server.csv` をもとに `make_filter_from_past_data.make_filter()` で作られる.
未知サーバへのリンクが見つかった場合に記録される(`crawler.parser()`)

## resultに作られるもの

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

### page_script_in_title.csv

タイトルの中に `script` 等の文字が含まれている怪しい系
`dealwebpage/script_analyze.py/script_inspection()` で呼び出される `title_inspection()` で判断される

### page_strange_script_name.csv

スクリプト名が怪しいものたちがまとめられる
`dealwebpage/script_analyze.py/script_inspection()` で呼び出される `script_name_inspection()` で判断される

### page_meta_refresh.csv

`<meta http-equiv="refresh` に類似する(`Refresh`, `rEfresh`)リダイレクトのコードが存在する場合に記録される
`dealwebpage/script_analyze.py/meta_refresh_inspection()` で調べる

### page_invisible_iframe.csv

目に見えないiframeが存在する場合に記録される
`dealwebpage/script_analyze.py/iframe_inspection()` で検査される

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

新規にできたページが記録される

### page_hash_same.csv

ハッシュ値が過去のものと一致するサイトが記録される

### page_hash_change.csv

ハッシュ値の変化したページが記録される

### page_after_redirect.csv

リダイレクトした際にリダイレクトもととリダイレクト後のURLが保存される

### file_new.csv

新規ファイルが記録される

### file_hash_same.csv

ハッシュ値が変化しなかったファイルが記録される

### file_hash_change.csv

ハッシュ値が変化したファイルが記録される

### file_different_size.csv

サイズが変化したファイルが記録される

### url_access_denied_by_robots.csv

robots.txt に検査を阻まれたURLたちが記録されていく

### error_failed_to_get_window_url.txt

別窓やタブが開いた際にURLを取るのに失敗したら記録される
どんなときに発生するのかよくわからん

### error_clamd.txt

Clamdで発生したエラーがまとめられている
