from queue import Queue
import pyclamd
import os
from time import sleep
from os import listdir
from threading import Thread
from collections import deque
from file_rw import w_file
from typing import Union, List

end = False          # メインプロセスから'end'が送られてくると終了
data_list = deque()   # 子プロセスから送られてきたデータリスト[(url, url_src, buff),(),()...]
clamd_error: List[str] = list()      # clamdでエラーが出たURLのリスト。100ごとにファイル書き込み。


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
            print('clamd process : receive end')
            end = True
            break
        else:
            data_list.append(recv)


def clamd_main(recvq: Queue[str], sendq: Queue[Union[str, bool]], org_path: str):
    # clamAVのデーモンが動いているか確認
    while True:
        try:
            print("clamd proc : connect to clamd, ", end="")
            # type: ignore
            cd = pyclamd.ClamdAgnostic()
            pin = cd.ping()
            print("connected")
            break
        except ValueError:
            print('wait for clamd starting ...')
            sleep(3)
        except Exception as e:
            pin = False
            print(e)
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
        except Exception as e:
            print('clamd : ERROR, URL = ' + url)
            clamd_error.append(url + '\n' + str(e))
        else:
            # 検知されると結果を記録
            if result is not None:
                w_file(org_path + '/alert/warning_clamd.txt', "{}\n\tURL={}\n\tsrc={}\n".format(result, url, url_src), mode="a")
                if not os.path.exists(org_path + '/clamd_files'):
                    os.mkdir(org_path + '/clamd_files')
                w_file(org_path + '/clamd_files/b_' + str(len(listdir(org_path + '/clamd_files'))+1) + '.clam',
                       url + '\n' + str(byte), mode="a")
            print('clamd : ' + url + ' have scanned.')

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
    print('clamd : ended')

    sendq.put('end')   # 親にendを知らせる
