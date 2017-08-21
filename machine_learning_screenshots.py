from time import sleep
from threading import Thread
from collections import deque
from file_rw import wa_file
from SVC_screenshot import preparation, main, prediction
import os

end = False          # メインプロセスから'end'が送られてくると終了
data_list = deque()  # 子プロセスから送られてきたデータのリスト[{url, url_src, 画像ファイル名, host名, 重要単語変化数},{辞書}, {辞書}...]


def receive(recvq):
    global end
    while True:
        recv = recvq.get(block=True)
        if recv == 'end':
            print('machine learning process : receive end')
            end = True
            break
        else:
            data_list.append(recv)


def screenshots_learning_main(recvq, sendq, path):
    classify_count = 0   # いくつのページを分類器にかけたか

    # 子プロセスからのデータを受信するスレッド
    t = Thread(target=receive, args=(recvq,))
    t.start()

    # 前回クローリング時のスクショを学習させる
    print('screenshots learning : start learning...')
    svc_dict = main.main(path)
    sendq.put('main : screenshots learning ended.')
    while True:
        if len(data_list) == 0:
            if end:
                break
            sleep(5)
            continue

        # データ取り出し
        data = data_list.popleft()
        url = data['url']
        src = data['src']
        img_name = data['img_name']
        host = data['host']
        num_diff_word = data['num_diff_word']

        # file_nameがFalseならば、スクショが撮れていない
        if img_name is False:
            continue

        # SVCがあるかどうか
        if host in svc_dict:
            classifier = svc_dict[host]
        else:
            continue

        # 保存したスクショをロード
        file_path = '../../RAD/screenshots/' + host + '/' + img_name + '.png'
        test_data = preparation.get_matrix_from_img(filename=file_path)
        if test_data is False:   # イメージのロードに失敗した場合
            continue
        test_data = list(test_data)

        # 予測
        classify_count += 1   # 検査したURL数
        result_df = prediction.prediction_main(classifier, test_data, url, src, num_diff_word)

        # 重要単語が8個以上変わっていて、かつスクショがそのサイトらしくなかった場合
        if result_df is not False:
            file_name = 'screenshots_inspection.csv'
            if os.path.exists(file_name):
                result_df.to_csv(file_name, mode='a', header=False, index=False)
            else:
                result_df.to_csv(file_name, mode='a', header=True, index=False)

    wa_file('num_of_checked_ByScreenshotsLearning.txt', str(classify_count) + '\n')

    # 終わりを告げる
    sendq.put('screenshots learning end')
    print('screenshots learning process : ended')
