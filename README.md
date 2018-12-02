# crawler

### ubuntuに変更したので、以下の記述からいろいろ変わってます。  


### 構成
* crawler/  
  * src/  
    * 各Pythonファイル  
    * files/
    * extensions/
  * organization/  
    * ritsumeikan/  
      * ROD/  
        * 各リスト  
  * ex/  
    * 今は使用していないファイル
      
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

### main.py  
実行例：python3 crawler/src/operate_main.py  ritsumeikan

