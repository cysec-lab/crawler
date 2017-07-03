# crawler

### 初期ファイル位置
* crawler/  
  * 各Pythonファイル  
  * decision_tree_tag/  
    * 機械学習Pythonファイル  
  * ROD/  
    * LIST/  
      * 各リスト  
    * mecab-dic/  
      * mecabで使う辞書  
      
### 必須ライブラリ
* BeautifulSoup4  
 スクレイピングに使う  

### 任意ライブラリ
以下は、ROD/LIST/SETTING.txtで使用しないように設定可能なため、その場合はいらない。  
でもインストールしていないとエラー出るかもなので、その場合はimport文をtryで囲むとかでいける?  
* mecab-python  
 形態素解析ツールMeCabをPythonで使うため。  
 mecab(本体)のインストール、path通しが必要。  
 mecab-dicはユーザ辞書としてNEologdを使っているが、windowsでコンパイルしたのでうまいこと動かないかも。  
* pyClamd  
 ClamAVのclamdをPythonで使うため。  
 ClamAVのインストール、clamdのpath通しが必要。  
* selenium  
 PhantomJSを使うため。  
 PhantomJSのインストールとpath通しが必要。 
* lxml  
 BeatuifulSoupで使う。  
 lxmlを入れていない場合は、html.parserが使われるので入れなくてもいい。(処理がhtml.parserより速いらしい)  
* scikit-learn  
 機械学習ライブラリ  
* numpy(mklつき？)  
 機械学習ライブラリで使う

### main.py
crawler/main.pyを実行。  

