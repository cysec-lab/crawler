import pyclamd
import os
from time import sleep
from os import listdir
from threading import Thread
from collections import deque
from file_rw import w_file

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

    # clamAVのclamdを起動(ubuntuにしたので、ずっと起動されている?)
    # p = Popen(["clamd"])

    while True:
        try:
            cd = pyclamd.ClamdAgnostic()
            pin = cd.ping()
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
        os._exit(0)    # 接続できなければ終わる

    # EICARテスト
    eicar = cd.EICAR()
    cd.scan_stream(eicar)

    t = Thread(target=receive, args=(recvq,))    # 子プロセスからのデータを受信するスレッド
    t.start()
    while True:
        if not data_list:
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
            if result is not None:
                w_file('../alert/warning_clamd.txt', str(result) + '\n' + url + '\nsrc= ' + url_src + '\n', mode="a")
                if not os.path.exists('../clamd_files'):
                    os.mkdir('../clamd_files')
                w_file('../clamd_files/b_' + str(len(listdir('../clamd_files'))+1) + '.clam', url + '\n' + str(byte),
                       mode="a")
            print('clamd : ' + url + ' have scanned.')
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
