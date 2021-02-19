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
    - [download_url.csv](#download_urlcsv)
    - [over_work_cpu.csv, over_work_memory.csv](#over_work_cpucsv-over_work_memorycsv)
    - [about_blank_url.csv](#about_blank_urlcsv)
    - [alert_text.csv](#alert_textcsv)
    - [new_window_url](#new_window_url)
    - [change_important_word.csv](#change_important_wordcsv)
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

- リダイレクトが発生した際にホワイトリストに含まれているかを調べて記録される
- なんかいまはうまく動いていない
  - ファイルのDLチェックページが開いたときを記録してそう
- `crawler_init.py` で作成
  - リダイレクト前URL, リダイレクト前URLのsrcURL, リダイレクト後URL, リダイレクト後URLの判定結果

### new_form_url.csv

- 入力フォームのaction先が未知サーバ(ホワイトリストにないaction先)の場合に記録する
- ActionにかかれているURLが不完全な場合には適度に修正( `webpage.py/comp_http` )
- `crawler.parser()` で作成される
- 辞書がまだ作られていないので作ってもいいかもしれない

TODO: 辞書作成の必要あり

### new_iframeSrc.csv

- 前回のクローリングで確認されなかったiframeが存在する場合に記録
  - `crawler.py` 591
- new_scriptSrc.csv
  - 前回のクローリングで確認されなかったscriptが使われているときに記録
  - `crawler.py` 640
- `inspection_page.iframe_inspection()` で探す
  - iframe の src が別である際にはそのURLsetが返ってくる

### new_page_without_frequent_word.csv

- 新たなページにあった単語が今まで見てきた同一サーバ内のの頻出単語にどれだけ含まれているか調査
- 類似性が全然ないならば記録する
- `crawler.py` 553

### url_history

- URLの遷移が存在する際に記録する
- `inspection_url_by_filter` を用いて怪しいURLかどうかチェックする
- `crawler.py` 922

### download_url.csv

自動ダウンロードが存在する場合に記録する

### over_work_cpu.csv, over_work_memory.csv

使用率が大きいプロセスを記録する

### about_blank_url.csv

- URL開いたらポップアップでファイルDLが出てくる者たちが記録されている...
- FileDLに記録されてない？
- `crawler.py` 1195

### alert_text.csv

- アラートででてきたURL, 内容が保存される
- `crawler.py` 1185

### new_window_url

- 新規ウィンドウを開く系ページを記録
- `crawler_init.py` 622

### change_important_word.csv

- 過去の記録と頻発する文字列が変わっていたならば記録する
- `crawler.py` 553

## organization の中に作成されるもの

### new_request_filter.json

`alertdir` の中の `new_request_url.csv` をもとに `make_filter_from_past_data.make_filter()` で作られる.

### new_link_filter.json

`alertdir` の中の `link_to_new_server.csv` をもとに `make_filter_from_past_data.make_filter()` で作られる.
未知サーバへのリンクが見つかった場合に記録される(`crawler.parser()`)
