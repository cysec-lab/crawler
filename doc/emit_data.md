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
