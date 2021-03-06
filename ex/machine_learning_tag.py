# from time import sleep
# from threading import Thread
# from collections import deque
# from file_rw import wa_file
# from decision_tree_tag import main, prediction, preparation
# from random import randint
# from copy import deepcopy
# import os
# from pandas import DataFrame
# from multiprocessing import Queue

# end = False          # メインプロセスから'end'が送られてくると終了
# data_list = deque()   # 子プロセスから送られてきたデータのリスト[{url, url_src, タグリスト, host名},{辞書}, {辞書}...]
# kaizan_list = list()


# def receive(recvq: Queue[str]):
#     global end
#     while True:
#         recv = recvq.get(block=True)
#         if recv == 'end':
#             print('machine learning process : receive end')
#             end = True
#             break
#         else:
#             data_list.append(recv)


# def check_tags(host, url, src,  tags, server_without_iframe_set, cannot_make_vec_server_set, tree_dict, sample):
#     # iframeタグがない場合
#     if ('iframe' not in tags) and ('invisible_iframe' not in tags):
#         return False
#     # 前回クローリング時にiframeが確認されていないserverの場合
#     if host in server_without_iframe_set:
#         if '!kaizan!' in url:
#             wa_file('../alert/kaizan_test.csv', url + '\n')
#         else:
#             wa_file('../alert/iframe_in_server_without_iframe_ByMachineLearning.csv', url + ',' + src + '\n')
#         return False
#     # 前回クローリング時のタグ情報ではベクトルがひとつも作れなかったserverだが、前はiframeがあった場合
#     if host in cannot_make_vec_server_set:
#         return False
#     # 決定木があるか
#     if host in tree_dict:
#         classifier = tree_dict[host]
#     else:
#         if '!kaizan!' in url:
#             wa_file('../alert/kaizan_test.csv', url + '\n')
#         else:
#             wa_file('new_server_ByMachineLearning.txt', host + ' is not found in tree_dict. ' +
#                     'This is new host, probably.\nURL = ' + url + '\nsource = ' + src + '\n')
#         return False
#     # タグの数がsample個以上ないとベクトル化できない
#     if len(tags) < sample * 2 + 1:
#         if '!kaizan!' in url:
#             wa_file('../alert/kaizan_test.csv', url + '\n')
#         else:
#             wa_file('../alert/appear_iframe_under20_tags_ByMachineLearning.csv', url + ',' + src + '\n')
#         return False
#     # 最初の10個以内にiframeタグがあったページは今のところない
#     if ('iframe' in tags[0:sample]) or ('invisible_iframe' in tags[0:sample]):
#         if '!kaizan!' in url:
#             wa_file('../alert/kaizan_test.csv', url + '\n')
#         else:
#             wa_file('../alert/iframe_in_0_' + str(sample) + '_ByMachineLearning.csv', url + ',' + src + '\n')
#         return False

#     return classifier


# def machine_learning_main(recvq: Queue[str], sendq, path):
#     result_data_frames = DataFrame()
#     sample = 10          # 前後いくつをベクトルにするか
#     sample2 = 0
#     classify_count = 0   # いくつのページを分類器にかけたか

#     # 子プロセスからのデータを受信するスレッド
#     t = Thread(target=receive, args=(recvq,))
#     t.start()

#     # 前回クローリング時のタグデータを学習させる
#     print('machine learning : start learning...')
#     tree_dict, tag_label_dict, server_without_iframe_set, cannot_make_vec_server_set = main.main(path, sample, sample2)
#     sendq.put('main : learning ended.')
#     while True:
#         if len(data_list) == 0:
#             if end:
#                 break
#             sleep(5)
#             continue

#         # データ取り出し
#         data = data_list.popleft()
#         url = data['url']
#         src = data['src']
#         tags = deepcopy(data['tags'])
#         host = data['host']

#         # 2/1000の確率でランダムな位置にiframeタグを挿入してみる(テスト)
#         rand = randint(1, 1000)
#         if rand == 500:
#             # ランダムな位置にiframeを挿入する
#             rand = randint(0, len(tags))
#             tags.insert(rand, 'iframe')
#             url = url + '!kaizan!iframe'
#             kaizan_list.append({'url': url, 'index': rand})
#         elif rand == 777:
#             # ランダムな位置にinvisible_iframeを挿入する
#             rand = randint(0, len(tags))
#             tags.insert(rand, 'invisible_iframe')
#             url = url + '!kaizan!invisible_iframe'
#             kaizan_list.append({'url': url, 'index': rand})

#         # 分類器にかけるかをチェックする
#         classifier = check_tags(host, url, src, tags, server_without_iframe_set, cannot_make_vec_server_set, tree_dict,
#                                 sample)
#         if classifier is False:
#             continue

#         # タグのリストをベクトル化してラベル付け(iframeタグとその周辺しかみない)
#         test_data, test_label_identifier = preparation.make_data(tags, tag_label_dict, url, sample, sample2,
#                                                                  crawling=True)
#         test_label = [i[0] for i in test_label_identifier]

#         # 予測
#         classify_count += 1   # 検査したURL数
#         result_df = prediction.prediction_main(classifier, test_data, test_label, url, src)

#         # 変な位置にiframeタグがあれば出力
#         if result_df is not False:
#             result_data_frames = result_data_frames.append(result_df)    # 多くなる可能性あるので最後にまとめてファイル出力
#             # iframeをそれ以外だと判断したものがあれば特にあやしい
#             if result_df['1->0'][0] or result_df['2->0'][0]:
#                 if '!kaizan!' in url:
#                     file_name = '../alert/kaizan_test.csv'
#                     if os.path.exists(file_name):
#                         result_df.to_csv(file_name, mode='a', header=False, index=False)
#                     else:
#                         result_df.to_csv(file_name, mode='a', header=True, index=False)
#                 else:
#                     file_name = '../alert/doubtful_iframe_ByMachineLearning.csv'
#                     if os.path.exists(file_name):
#                         result_df.to_csv(file_name, mode='a', header=False, index=False)
#                     else:
#                         result_df.to_csv(file_name, mode='a', header=True, index=False)

#     # ファイル書き込み
#     if not result_data_frames.empty:
#         file_name = 'iframe_inspection_ByMachineLearning.csv'
#         if os.path.exists(file_name):
#             result_data_frames.to_csv(file_name, mode='a', header=False, index=False)
#         else:
#             result_data_frames.to_csv(file_name, mode='a', header=True, index=False)
#     wa_file('num_of_checked_url_ByMachineLearning.txt', str(classify_count) + '\n')
#     text = ''
#     for i in kaizan_list:
#         text += i['url'] + ',' + str(i['index']) + '\n'
#     wa_file('../alert/kaizan_list.csv', text)

#     # 終わりを告げる
#     sendq.put('machine learning end')
#     print('machine learning process : ended')
