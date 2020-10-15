from collections import deque
from queue import Queue
from threading import Thread, Event
from file_rw import w_file
from os import path, mkdir

data_list = deque()
event = Event()


def receive_alert(recv_q: Queue[str]):
    while True:
        recv_data = recv_q.get(block=True)
        data_list.append(recv_data)
        event.set()
        if recv_data == 'end':
            print('summarize_alert process : receive end')
            break


def summarize_alert_main(recv_q: Queue[str], send_q: Queue[str], nth: int, org_path: str):

    alert_dir_path = org_path + '/alert'
    # alertディレクトリを作成
    if not path.exists(alert_dir_path):
        mkdir(alert_dir_path)

    t = Thread(target=receive_alert, args=(recv_q,))  # 他プロセスからのデータを受信するスレッド
    t.start()

    while True:
        if not data_list:
            event.clear()   # data_listが空になると同時にreceiveで'end'がappendされたらデッドロックなる？
            event.wait()    # data_listが空(if文の中に入る) -> receive_alert()の中でsetされると、wait()が終わる

        temp = data_list.popleft()
        if temp == 'end':
            break

        url = temp['url']
        # url_src = temp['src']
        file_name = temp['file_name']
        content = temp['content']
        label = temp['label']

        # label と content にnthを追加
        label = 'Nth,' + label
        content = str(nth) + ',' + content

        # "falsification.cysec.cs.ritsumei.ac.jp"がURLに含まれる場合、ファイル名を変更する
        if ("falsification.cysec.cs.ritsumei.ac.jp" in url) or ("192.168.0.233" in url):
            file_name = "TEST_" + file_name

        # label と content を出力
        if file_name.endswith('.csv'):
            if not path.exists(alert_dir_path + '/' + file_name):
                w_file(alert_dir_path + '/' + file_name, label + '\n', mode="a")
            w_file(alert_dir_path + '/' + file_name, content + '\n', mode="a")
        else:
            w_file(alert_dir_path + '/' + file_name, content + '\n', mode="a")

    print('summarize_alert : ended')

    send_q.put('end')   # 親にendを知らせる
