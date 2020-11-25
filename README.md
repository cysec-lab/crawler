# crawler

※ 2019/2/9に無駄なコードを消すためにソースコードを変更したことで、クローリングが終わらなくなってしまいました
(forced_termination()内でループから抜け出せていなかった)。
原因は、クローリングプロセスの一つが、いつまでたっても終了しなかったため。  
無限ループに入り、クローリングが終了しない場合は、commitのコメントがXXXになっているファイルを、2/9より前のバージョンのファイルに戻してください。  

ファイルバージョンを現在戻してとりあえず動くものを作っている

### 初期構成

```
crawler/
  ├- src/
  |  ├- Pythonファイル
  |  ├- webdrivers/
  |  |  └- ヘッドレスブラウザに関わるコードたち
  |  ├- utils/
  |  |  └- 雑多
  |  ├- checkers/
  |  |  └- ページの内容調査に関わるコードたち
  |  ├- dealwebpage/
  |  |  └- webpageの内容取得に関わるコードたち
  |  |
  |  ├- tests/
  |  |  └- ユニットテストたち
  |  ├- files/
  |  |  └- クローリングプロセスで使用するファイル
  |  └- extensions/
  |      ├- CrawlerExtension.xpi
  |      └- CrowlerExtension/
  |          └- 拡張機能のソースファイル
  ├- organization/
  |  └- ritsumeikan/
  |      └- ROD/
  |          └- 各リスト
  ├- falsification/
  |  ├- test_site/
  |  |  └- 研究室内自作改ざんサイト(falsification.cysec.cs.ritsumei.ac.jp)のHTML
  |  └- mal_site/
  |      └- 研究室内自作悪性サーバ(192.168.0.233)のHTML
  └ ex/
       └今は使用していないファイル
```

organization/ritsumeikan/の中にクローリング結果が保存されていく。  
研究室内自作改ざんサイトや悪性サーバは、proxmox上に作っている。


### 必須ライブラリ
* BeautifulSoup4  
 スクレイピングに使う  
* psutil  
 リソース監視に使う  

### 任意ライブラリ
以下は、ROD/LIST/SETTING.txtで使用しないように設定可能なため、その場合はいらない。  
でもインストールしていないとimport文でエラー出るかもなので、その場合はimport文をtryで囲むとかでいける  
* mecab-python  
 形態素解析ツールMeCabをPythonで使うため。  
 mecab(本体)のインストール
* pyClamd  
 ClamAVのclamdをPythonで使うため。  
 ClamAVのインストール 
* selenium  
 ヘッドレスブラウザ(Firefox)を使うため。 
 Ubuntu16.04LTS のPython3なら最初から入っている。  
 Firefoxを使うためには、geckodriverが必要。
* lxml  
 BeatuifulSoupで使う。  
 lxmlを入れていない場合は、html.parserが使われるので入れなくてもいい。(lxmlはhtml.parserより処理が速いらしい)  

### 設定ファイル

- DOMAIN.json
  - allow: 検索を許可するドメイン名(リスト)。ドメイン名がこの文字列で終わるURLは組織内とする。
  - deny: 検索しないドメイン名(リスト)。ドメイン名が以下の文字列で終わるURLは検索しない。
- WHITE.json
- ホスト名: パス(リスト)。ホスト名のURLで、リストの文字列を含む場合はクローリングする。
- IPAddress.json
  - allow: 検索を許可するIPアドレス(リスト)。
- REDIRECT.json
  - allow: リダイレクト後として安全なホスト名の辞書。keyはホスト名(の後半部分)。valueはパス(の途中)のリスト。
  - deny: リダイレクト後として危険なホスト名の辞書。(処理は未実装)
- BLACK.json
  - 文字のリスト。この文字を含むURLは検索しない。

### 実行方法  
実行ファイル名 ： operate_main.py  
引数 ： 組織名(crawler/organization/以下にあるディレクトリ名)
### 例  
python3 crawler/src/operate_main.py  ritsumeikan

### 注意
anacondaなどの仮想環境を使うと面倒くさくなる。  
理由は、operate_main.pyの一番最初でmultiproccessingのfork方法をspawnに変更しているから。  
仮想環境だとこの一文でエラーが出たと思う。  

### 実行結果の保存場所とその中にあるディレクトリの説明  
以下は、crawler/organization/組織名/の中に全て保存される。  
* ROD/LIST  
  クローリングするURLを判別するためのリストが保存されている。
* ROD/df_dicts  
  過去のクローリングで集めた、サーバごとの単語データ。ディレクトリ名の数字は何回目のクローリングのデータかを表している。
* ROD/url_hash_json  
  過去のクローリングで集めた、サーバごとのデータ
* RAD  
  実際にクローリングで使用するRODのデータ。クローリングを開始直前にRODの内容をコピーして、クローリング中に書き換えながら使用する。クローリングが終わると、ディレクトリ名をRODに変更し、元のRODに上書きをする。
* result  
  何回か途中保存しているため、下層にいくつか保存ディレクトリがある(result_1，result_2・・・)  
  result_2はresult_1の結果の続きであり、result_1の結果を含まない 
* result/Download  
  クローリング中に自動ファイルダウンロードによってダウンロードされたファイルの保存場所
* result/CPU、 result/MEM  
  CPUやメモリ使用状況の調査結果保存場所
* result/achievement  
  result/result_*の各ディレクトリに分かれているファイルをまとめた結果。クローリング完了時に作成される。  
  同じファイル名のデータを1つのファイルに統合する。
* alert  
  怪しいと判断されたページの情報を各ファイルに保存する
* result_history  
  過去のクローリング結果の履歴(resultのディレクトリ名を数字(通し番号)に変更したもの)

### テストケース実行

src ディレクトリに移動して実行する必要あり...なんでだろう

`python -m unittest discover tests -v`

## 出力内容

- CPU
  - .pickleで保存されたデータ
- MEM
  - .pickleで保存されたデータ
- achievement
  - 何回かに分けてクローリングされた結果がまとめられる
- result_*
  - 何回かに分けてクローリングされた結果が入る

### achievementの中

- after_redirect.csv
  - リダイレクトの内容を保存
  - `crawler_init.py` で作成
  - リダイレクト前URL, リダイレクト前URLのsrcURL, リダイレクト後URL, リダイレクト後URLの判定結果
- inivisible_iframe.csv
  - HTML のインラインフレーム要素 (<iframe>) 入れ子になった閲覧コンテキストを表現する
  - width、height属性値が0か display:none か visibility:hidden が設定されている等、目に見えない <iframe> が記録される
- new_page.csv
  - `crawler.py/parse()` で作成
  - url_dict に存在しないページの場合これは新規ページ
- same_hash_page.csv
  - `crawler.py/parse()` で作成
  - url_dict に存在するSHAと新たに取得したSHAが一致するかを調べて作成
- change_hash_page.csv
  - `crawler.py/parse()` で作成
  - Hash値が変わったページに関して何日で変わったかを記録する
- script_name.csv
  - スクリプト名が1文字のとき、怪しいスクリプト名のときに記録する
  - タイトル内に `<script ` が存在しているとき
  - `src/crawler.py/` 618行目
  - `src/dealwebpage/inspection_page.py/script_inspection()`
- clamd_error.txt
  - clamdで起きたエラーをまとめて記録する
  - 大きすぎるファイル等々記録される
- meta_refresh.csv
  - `crawler.py/parse()` で作成
  - アドレス変更等で飛ばされた場合に記録する
- server
  - 各サーバの結果が入る
- hack_word_Lv*.txt
  - ハック関連の文字列があるときにレベルに応じて記録される
- new_file.csv
  - `crawler.py/parse()` で作成
  - url_dict に存在しないページの場合これは新規ファイル
- result.txt
  - 達成URL数を全部まとめて記録する
- notice.txt
  - 特殊なケースとしてなんかKillされた時等に記録されるページ

### alertの中身

- new_form_url.csv
  - 入力フォームのaction先が未知サーバの場合に記録する
  - ActionにかかれているURLが不完全な場合には適度に修正( `webpage.py/comp_http` )
- request_to_new_server.csv
  - リクエスト先のURLが安全かを調べる
- download_url.csv
  - 自動ダウンロードが存在する場合に記録する
- over_work_cpu.csv, over_work_memory.csv
  - 使用率が大きいプロセスを記録する
- url_history.csv
  - URLの遷移が存在する際に記録する
  - `inspection_url_by_filter` を用いて怪しいURLかどうかチェックする
  - `crawler.py` 922
- about_blank_url.csv
  - URL開いたらポップアップでファイルDLが出てくる者たちが記録されている...
  - FileDLに記録されてない？
  - `crawler.py` 1195
- alert_text.csv
  - アラートででてきたURL, 内容が保存される
  - `crawler.py` 1185
- new_form_url.csv
  - 未知サーバにフォームを送信しているページを記録する
  - `crawler.py` 675
- new_page_without_frequent_word.csv
  - 新たなページにあった単語が今まで見てきた同一サーバ内のの頻出単語にどれだけ含まれているか調査
  - 類似性が全然ないならば記録する
  - `crawler.py` 553
- after_redirect_check.csv
  - リダイレクトが発生した場合ホワイトリストに含まれているかを調べて記録する
  - `crawler_init.py` 649
- new_window_url
  - 新規ウィンドウを開く系ページを記録
  - `crawler_init.py` 622
- change_important_word.csv
  - 過去の記録と頻発する文字列が変わっていたならば記録する
  - `crawler.py` 553
- link_to_new_server.csv
  - 未知サーバへのリンクが存在する場合に記録する
- new_iframeSrc.csv
  - 前回のクローリングで確認されなかったiframeが存在する場合に記録
  - `crawler.py` 591
- new_scriptSrc.csv
  - 前回のクローリングで確認されなかったscriptが使われているときに記録
  - `crawler.py` 640
