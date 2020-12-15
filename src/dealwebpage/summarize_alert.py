from __future__ import annotations

from logging import getLogger
from multiprocessing import Queue
from os import mkdir, path
from queue import Queue as threadQueue
from threading import Thread
from typing import Any, Union, cast

from utils.alert_data import Alert
from utils.file_rw import w_file

logger = getLogger(__name__)

def receive_alert(recv_q: Queue[Union[str, Alert]], data_list: threadQueue[Any]):
    """
    他プロセスからのアラートデータを受信するスレッド

    Args:
    - reqv_q: 他のプロセスからのアラートを受け取るためのキュー
    """
    while True:
        recv_data = recv_q.get(block=True)
        data_list.put(recv_data)
        if recv_data == 'end':
            # 終了処理
            logger.info("Summarize alert: Receive end")
            break


def summarize_alert_main(recv_q: Queue[Union[Alert, str]], send_q: Queue[str], nth: int, org_path: str):
    """
    Alertが出た場合に記録するためのプロセス

    Args:
    - recv_q: 各プロセスからのアラートデータを受け取るためのキュー, endがきたら終了
    - send_q: 
    - nth: 
    - org_path: organizationのパス
    """

    alert_dir_path = org_path + '/alert'
    # alertディレクトリを作成
    if not path.exists(alert_dir_path):
        mkdir(alert_dir_path)

    # アラート受信スレッドとの通信用キュー
    data_list: threadQueue[Any] = threadQueue()

    t = Thread(target=receive_alert, args=(recv_q, data_list))
    t.daemon = True
    t.start()

    while True:
        if not data_list.empty():
            temp = data_list.get()
            if temp == 'end':
                logger.info('receive end!!')
                data_list.task_done()
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

            data_list.task_done()

    data_list.join()
    logger.info("Summarize_alert: FIN")

    send_q.put('end')   # 親にendを知らせる
