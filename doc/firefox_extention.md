# Firefox_setting

作成したFirefox拡張機能に関するメモ。
拡張機能の基本動作は、Wathcer.htmlというページを開いておき、そのページに作成したボタンをクローラが操作することで、レンダリング時のブラウザ内情報を収集する。

## 概要

1. クローラはCreate New Tabボタンをクリックし、about:blankのタブを開く。
2. クローラはStart Watchingボタンをクリックする。
3. クローラはabout:blankのタブでURLに接続し、Firefoxはウェブページをレンダリングする。
4. クローラはStop Watchingボタンをクリックし、拡張機能のaddDataToHtml.jsがWatcher.htmlのdivタブ(id="contents")内に収集したデータを書き込む。
5. クローラは書き込んだデータを読む。
6. クローラはClear Contentsボタンをクリックし、Wathcer.htmlに書き込んだデータを削除する。

次のURLに接続する際には最初に戻る。

## 各ファイル説明

###  Wathcer.html

以下の4つのボタンがある。
1. Create New Tab ： (about:blank)のページを開く。クローラはそのblankタブにURLを入力してウェブページにアクセスする。
2. Start Watching ： background.jsで監視を開始する。
3. Stop Watching : backgound.jsでの監視を止め、収集したデータをWathcer.htmlのdivタブ(id="contents")内に書き込む。
4. Clear Contetns : divタブ(id="contents")内に書き込んだデータを削除する。

### background.js

Firefoxのバックグラウンドで動き続ける。
Start Watchingボタンが押されてから、Stop Watchingボタンが押されるまでの間、Firefox内の特定のイベントを監視する。
収集したデータはStop Watchingボタンが押されるまで保持しておき、それがクリックされたときにaddDataToHTML.jsに収集したデータを送信する。

### attachJs.js

Watcher.htmlの各ボタンにJavaScriptの関数を割り当てる。
動的に割り当てないと、関数が実行されなかった。(たしか)

### addDataToHtml.js

Stop Watchingボタンが押された時に、Watcher.htmlのHTMLに収集したデータを書き込む。
