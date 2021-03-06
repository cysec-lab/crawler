# loggerについて

loggerはクローリングの情報を出力するのとデバッグのためにつけた

crawlerでは多くのプロセスからログを排出することとなるため、
複数プロセスから単一ファイルへの同時アクセス手段がないPythonでは一つのプロセスにログをまとめて
そこでファイルへ書き込む手段を用いている.

`utils/logger.py/log_listener_process()` プロセスがログを受け取るプロセスであり,
キューを用いて通信を行っている.
最終的にはキューに`None` を入れることでこのプロセスが終了する

各プロセスは起動時に `utils/logger.py/worker_configurer()` を用いて
ログをリスナープロセスに飛ばすように設定する.
スレッド等ではとくに設定の必要はなく`logging.getLogger()`で勝手にログがまとめてもらえる

## 現在の問題点

現在の実装は本来のloggingスタイルとは少しずれたものとなっている

### 起きている弊害

- すべてのフルログをとれているわけではない
  - 本来はseleniumのログ等も全て取れるが取れていない

### なぜこの実装になっているか

- 実装したクローラ自体のログはすべて取れる
- ログが途中から排出されなくなる不具合がおきて原因を突き止められなかったため
  - 実行中になぜかログだけ排出されずクローリングは継続する
- 本来であればselenium等のログも取得するべきだがログが出ないよりかはまし。
  - 上原先生曰く「ログは多いに越したことはない」
- ここに時間を割くよりはほかに割きたかった

### 本来すべき実装

Loggingクックブックに書かれている実装にすることですべてのログが取れるようになる

https://docs.python.org/3/howto/logging-cookbook.html#logging-to-a-single-file-from-multiple-processes
