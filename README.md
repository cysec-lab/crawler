# crawler

※ 2019/2/9に無駄なコードを消すためにソースコードを変更したことで、クローリングが終わらなくなってしまいました
(forced_termination()内でループから抜け出せていなかった)。
原因は、クローリングプロセスの一つが、いつまでたっても終了しなかったため。  
無限ループに入り、クローリングが終了しない場合は、commitのコメントがXXXになっているファイルを、2/9より前のバージョンのファイルに戻してください。  

ファイルバージョンを現在戻してとりあえず動くものを作っている

## 初期構成

```text
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

- hash_changeBeautifulSoup4
  - スクレイピングに使う  
- hash_changepsutil
  - リソース監視に使う

### 任意ライブラリ

以下は、ROD/LIST/SETTING.txtで使用しないように設定可能なため、その場合はいらない。  
でもインストールしていないとimport文でエラー出るかもなので、その場合はimport文をtryで囲むとかでいける  

- hash_changemecab-python
  - 形態素解析ツールMeCabをPythonで使うため。
  - mecab(本体)のインストール
- hash_changepyClamd
  - ClamAVのclamdをPythonで使うため。
  - ClamAVのインストール
- hash_changeselenium
  - ヘッドレスブラウザ(Firefox)を使うため。
  - Ubuntu16.04LTS のPython3なら最初から入っている。
  - Firefoxを使うためには、geckodriverが必要。
- hash_changelxml
  - BeatuifulSoupで使う。
  - lxmlを入れていない場合は、html.parserが使われるので入れなくてもいい。(lxmlはhtml.parserより処理が速いらしい)  

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
- ONLY.json
  - クローリング対象のURLを制限する
  - クローリング対象にしたいURLの正規表現を書いていくと当てはまるURLのみをクローリングする
  - `{ "Regex": [regex1, regex2...]}`

### 実行方法

- 実行ファイル名 ： operate_main.py
- 引数 ： 組織名(crawler/organization/以下にあるディレクトリ名)

### 例

`python3 crawler/src/operate_main.py  ritsumeikan`

### 注意

anacondaなどの仮想環境を使うと面倒くさくなる。
理由は、operate_main.pyの一番最初でmultiproccessingのfork方法をspawnに変更しているから。
仮想環境だとこの一文でエラーが出たと思う。

### 実行結果の保存場所とその中にあるディレクトリの説明

以下は、crawler/organization/組織名/の中に全て保存される。

- hash_changeROD/LIST
  - クローリングするURLを判別するためのリストが保存されている。
- hash_changeROD/df_dicts
  - 過去のクローリングで集めた、サーバごとの単語データ
  - ディレクトリ名の数字は何回目のクローリングのデータかを表している。
- hash_changeROD/url_hash_json
  - 過去のクローリングで集めた、サーバごとのデータ
- hash_changeRAD
  - 実際にクローリングで使用するRODのデータ
  - クローリングを開始直前にRODの内容をコピーして、クローリング中に書き換えながら使用する。クローリングが終わると、ディレクトリ名をRODに変更し、元のRODに上書きをする
- hash_changeresult
  - 何回か途中保存しているため、下層にいくつか保存ディレクトリがある(result_1，result_2・・・)
  - result_2はresult_1の結果の続きであり、result_1の結果を含まない
- hash_changeresult/Download
  - クローリング中に自動ファイルダウンロードによってダウンロードされたファイルの保存場所
- hash_changeresult/CPU、 result/MEM
  - CPUやメモリ使用状況の調査結果保存場所
- hash_changeresult/achievement
  - result/result_*の各ディレクトリに分かれているファイルをまとめた結果。クローリング完了時に作成される。
  - 同じファイル名のデータを1つのファイルに統合する。
- hash_changealert
  - 怪しいと判断されたページの情報を各ファイルに保存する
- hash_changeresult_history
  - 過去のクローリング結果の履歴(resultのディレクトリ名を数字(通し番号)に変更したもの)

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
