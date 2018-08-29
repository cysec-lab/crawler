from collections import deque
from threading import Thread, Event
from file_rw import wa_file
from os import path, mkdir

data_list = deque()
event = Event()


def receive_alert(recv_q):
    while True:
        recv_data = recv_q.get(block=True)
        data_list.append(recv_data)
        event.set()
        if recv_data == 'end':
            print('summarize_alert process : receive end')
            break


def summarize_alert_main(recv_q, send_q, nth):

    alert_dir_path = '../../alert'
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
        url_src = temp['src']
        file_name = temp['file_name']
        content = temp['content']
        label = temp['label']

        # label と content にnthを追加
        label = 'Nth,' + label
        content = str(nth) + ',' + content

        # label と content　を直うち
        if file_name.endswith('.csv'):
            if not path.exists(alert_dir_path + '/' + file_name):
                wa_file(alert_dir_path + '/' + file_name, label + '\n')
            wa_file(alert_dir_path + '/' + file_name, content + '\n')
        else:
            wa_file(alert_dir_path + '/' + file_name, content + '\n')

    print('summarize_alert : ended')

    send_q.put('end')   # 親にendを知らせる
