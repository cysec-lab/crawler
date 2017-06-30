﻿import pyclamd
from time import sleep
from os import listdir
from threading import Thread
from subprocess import Popen
from collections import deque
from file_rw import wa_file

end = False          # メインプロセスから'end'が送られてくると終了
data_list = deque()   # 子プロセスから送られてきたデータリスト[(url, url_src, buff),(),()...]
clamd_error = list()      # clamdでエラーが出たURLのリスト。100ごとにファイル書き込み。


def receive(recvq):
    global end
    while True:
        recv = recvq.get(block=True)
        if recv == 'end':
            print('clamd process : receive end')
            end = True
            break
        else:
            data_list.append(recv)


def clamd_main(recvq, sendq):

    # clamAVのclamdを起動
    p = Popen(["clamd"])
    while True:
        try:
            cd = pyclamd.ClamdAgnostic()
            pin = cd.ping()
            break
        except ValueError:
            print('wait for clamd starting ...')
            sleep(3)
        except Exception as e:    # ウイルスデータの更新のwarningはキャッチできない
            pin = False
            print(e)
            break
    sendq.put(pin)

    # EICARテスト
    eicar = cd.EICAR()
    cd.scan_stream(eicar)

    t = Thread(target=receive, args=(recvq,))    # 子プロセスからのデータを受信するスレッド
    t.start()
    while True:
        if len(data_list) == 0:
            if end:
                break
            sleep(3)
            continue
        temp = data_list.popleft()
        url = temp[0]
        url_src = temp[1]
        byte = temp[2]
        try:
            result = cd.scan_stream(byte)
        except Exception as e:
            print('clamd : ERROR, URL = ' + url)
            clamd_error.append(url + '\n' + str(e))
        else:
            if not (result is None):
                wa_file('warning_clamd.txt', str(result) + '\n' + url + '\nsrc= ' + url_src + '\n')
                wa_file('clamd_files/' + str(len(listdir('clamd_files'))) + '.clam', url + '\n' + str(byte))
            print('clamd : ' + url + ' have scanned.')
        if len(clamd_error) > 100:
            text = ''
            for i in clamd_error:
                text += i + '\n'
            wa_file('clamd_error.txt', text)
            clamd_error.clear()

    text = ''
    for i in clamd_error:
        text += i + '\n'
    wa_file('clamd_error.txt', text)
    clamd_error.clear()

    cd.shutdown()    # clamdにシャットダウンシグナル送信
    while p.poll() is None:   # Noneの間は生きている
        sleep(3)
    print('clamd : ended')
    sendq.put('end')
