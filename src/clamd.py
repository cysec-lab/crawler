from __future__ import annotations

import os
from collections import deque
from logging import getLogger
from multiprocessing import Queue
from os import listdir
from threading import Thread
from time import sleep
from typing import Any, List, Union

import pyclamd

from utils.file_rw import w_file
from utils.logger import worker_configurer

end = False                     # メインプロセスから'end'が送られてくると終了
data_list = deque()             # 子プロセスから送られてきたデータリスト[(url, url_src, buff),(),()...]
clamd_error: List[str] = list() # clamdでエラーが出たURLのリスト。100ごとにファイル書き込み。

logger = getLogger(__name__)

def receive(recvq: Queue[str]):
    """
    "end"が送られてくるまで、データを受信する

    args:
        reqvq: キュー
    """
    global end
    while True:
        recv = recvq.get(block=True)
        if recv == 'end':
            logger.info('Clamd Process received end')
            end = True
            break
        else:
            data_list.append(recv)


def clamd_main(queue_log: Queue[Any], recvq: Queue[str], sendq: Queue[Union[str, bool]], org_path: str):
    worker_configurer(queue_log, logger)
    # clamAVのデーモンが動いているか確認
    while True:
        try:
            logger.info('Clamd Process connect...')
            cd = pyclamd.ClamdAgnostic()
            pin = cd.ping()
            logger.info('Clamd Process connected!!!')
            break
        except ValueError:
            logger.info('Clamd Process waiting for clamd start....')
            sleep(3)
        except Exception as err:
            pin = False
            logger.exception(f'Exception has occur: {err}')
            break
    sendq.put(pin)   # 親プロセスにclamdに接続できたかどうかの結果を送る
    if pin is False:
        os._exit(0) # type: ignore # 接続できなければ終わる

    # EICARテスト
    eicar = cd.EICAR() # type: ignore
    cd.scan_stream(eicar) # type: ignore

    t = Thread(target=receive, args=(recvq,))    # クローリングプロセスからのデータを受信するスレッド
    t.start()
    while True:
        if not data_list:
            if end:
                break
            # クローリングプロセスからデータが送られていなければ、3秒待機
            sleep(3)
            continue
        temp = data_list.popleft()
        url = temp[0]
        url_src = temp[1]
        byte = temp[2]
        # clamdでスキャン
        try:
            result = cd.scan_stream(byte) # type: ignore
        except Exception as err:
            logger.exception('Exception has occur, URL={url}, {err}')
            clamd_error.append(url + '\n' + str(err))
        else:
            # 検知されると結果を記録
            if result is not None:
                w_file(org_path + '/alert/warning_clamd.txt', "{}\n\tURL={}\n\tsrc={}\n".format(result, url, url_src), mode="a")
                if not os.path.exists(org_path + '/clamd_files'):
                    os.mkdir(org_path + '/clamd_files')
                w_file(org_path + '/clamd_files/b_' + str(len(listdir(org_path + '/clamd_files'))+1) + '.clam',
                       url + '\n' + str(byte), mode="a")
            logger.info('clamd have scanned: %s', url)

        # エラーログが一定数を超えると外部ファイルに書き出す
        if len(clamd_error) > 100:
            text = ''
            for i in clamd_error:
                text += i + '\n'
            w_file('clamd_error.txt', text, mode="a")
            clamd_error.clear()

    text = ''
    for i in clamd_error:
        text += i + '\n'
    w_file('clamd_error.txt', text, mode="a")
    clamd_error.clear()

    logger.debug("Clamd end")
    sendq.put('end')   # 親にendを知らせる
