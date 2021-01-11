# 重要なグローバル変数についてのメモ

## crawler_init.py

### hostName_achievement

各ホスト名をキーに到達したURL数が記録される辞書
make_process() にて初めて探索するホストの際に作成される.
子プロセスから `links` を `receive_and_send()` が受信すると `+1` される.

### hostName_remaining

各ホストの探索対象URLを記録した辞書
`allocate_to_host_remaining()` で探索URLリストが更新される
`receive_and_send()` で探索リストからURLが取り出されてクローリングプロセスに割り当てられる

```text
hostName_remaining
├- [host1]
│   ├- URL_list : URLの待機リスト
│   └- update_time: 待機リストからURLが最後に取り出された時間
├- [host2]
│   ├- URL_list
│   └- update_time
│
└- [hostX]
```
