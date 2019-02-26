# crawler


### 構成
crawler/  
　┣ src/  
　┃　┣ Pythonファイル  
　┃　┣ files/  
　┃　┃　┗ クローリングプロセスで使用するファイル  
　┃　┗ extensions/  
　┃　　　┣ CrawlerExtension.xpi  
　┃　　　┗ CrowlerExtension/  
　┃　　　　　┗ 拡張機能のソースファイル  
　┣ organization/  
　┃　┗ ritsumeikan/  
　┃　　　┗ ROD/  
　┃　　　　　┗ 各リスト  
　┗ ex/  
　　　┗今は使用していないファイル  
    
organization/ritsumeikan/の中にクローリング結果が保存されていく
      
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
 lxmlを入れていない場合は、html.parserが使われるので入れなくてもいい。(処理がhtml.parserより速いらしい)  

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
crawler/organization/組織名/の中に全て保存される  
* ROD/LIST  
  。
* ROD/df_dicts  
  
* ROD/url_hash_json  

* RAD  
  実際にクローリングで使用するRODのデータ。RODをコピーして、クローリング中に書き換えながら使用する。クローリングが終わると、ディレクトリ名をRODに変更し、元のRODに上書きをする。
* result  
  何回か途中保存しているため、いくつか保存ディレクトリがある
* alert  

* result_history  