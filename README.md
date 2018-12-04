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
 Firefoxを使うためには、geckdriverが必要。
* lxml  
 BeatuifulSoupで使う。  
 lxmlを入れていない場合は、html.parserが使われるので入れなくてもいい。(処理がhtml.parserより速いらしい)  

### 実行例  
python3 crawler/src/operate_main.py  ritsumeikan  

### 注意
anacondaなどの仮想環境を使うと面倒くさくなる。  
理由は、operate_main.pyの一番最初でmultiproccessingのfork方法をspawnに変更しているから。  
仮想環境だとこの一文でエラーが出たと思う。

