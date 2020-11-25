from __future__ import annotations

from collections import deque
from logging import getLogger
from multiprocessing import Queue
from os import mkdir, path
from threading import Event, Thread
from typing import Any, Union, cast

from utils.alert_data import Alert
from utils.file_rw import w_file
from utils.logger import worker_configurer

data_list: deque[Union[str, Alert]] = deque()
event = Event()

logger = getLogger(__name__)

def receive_alert(recv_q: Queue[Union[str, Alert]]):
    """
    他プロセスからのアラートデータを受信するスレッド

    Args:
    - reqv_q: 他のプロセスからのアラートを受け取るためのキュー
    """
    while True:
        recv_data = recv_q.get(block=True)
        data_list.append(recv_data)
        event.set()
        if recv_data == 'end':
            # 終了処理
            logger.info("Summarize alert: Receive end")
            break


def summarize_alert_main(queue_log: Queue[Any], recv_q: Queue[Union[Alert, str]], send_q: Queue[str], nth: int, org_path: str):
    """
    Alertが出た場合に記録するためのプロセス

    Args:
    - recv_q: 各プロセスからのアラートデータを受け取るためのキュー, endがきたら終了
    - send_q: 
    - nth: 
    - org_path: organizationのパス
    """
    worker_configurer(queue_log, logger)
    alert_dir_path = org_path + '/alert'
    # alertディレクトリを作成
    if not path.exists(alert_dir_path):
        mkdir(alert_dir_path)

    t = Thread(target=receive_alert, args=(recv_q,))
    t.setDaemon(True)
    t.start()

    while True:
        if not data_list:
            event.clear()   # data_listが空になると同時にreceiveで'end'がappendされたらデッドロックなる？
            event.wait()    # data_listが空(if文の中に入る) -> receive_alert()の中でsetされると、wait()が終わる

        temp = data_list.popleft()
        if temp == 'end':
            break

        alert = cast(Alert, temp)

        file_name = alert.file_name
        content = alert.content
        label = alert.label

        # label と content にnthを追加
        label = 'Nth,' + label
        content = str(nth) + ', ' + content

        # "falsification.cysec.cs.ritsumei.ac.jp"がURLに含まれる場合、ファイル名を変更する
        if ("falsification.cysec.cs.ritsumei.ac.jp" in alert.url) or ("192.168.0.233" in alert.url):
            file_name = "TEST_" + file_name

        # label と content を出力
        if file_name.endswith('.csv'):
            if not path.exists(alert_dir_path + '/' + file_name):
                w_file(alert_dir_path + '/' + file_name, label + '\n', mode="a")
            w_file(alert_dir_path + '/' + file_name, content + '\n', mode="a")
        else:
            w_file(alert_dir_path + '/' + file_name, content + '\n', mode="a")

    logger.info("Summarize_alert: end")

    send_q.put('end')   # 親にendを知らせる
