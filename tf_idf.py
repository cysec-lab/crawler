import os
import json
from math import log
import pickle
from collections import Counter

"""
クローリング後にサーバごとの
tf-idf値
ページのロードに行ったリクエストのURL集合
iframeのsrc先URLの集合
をまとめて保存する
"""


def make_and_save_host_idf_dict():
    df_dict = dict()   # {server : {単語:df値, 単語:df値, ...}, server : {df辞書}, ... , server : {df辞書} }
    try:
        os.mkdir('ROD/idf_dict')
    except FileExistsError:
        pass
    os.chdir('ROD/df_dicts/')   # このフォルダ以下の全てのdfフォルダをマージしてidf辞書を作る
    dir_list = os.listdir()
    for df_dict_dir in dir_list:
        json_file_list = os.listdir(df_dict_dir)
        for json_file in json_file_list:
            f = open(df_dict_dir + '/' + json_file, 'r')
            dic = json.load(f)   # df辞書ロード
            f.close()
            if len(dic) == 0:  # 中身がなければ次へ
                continue
            if json_file not in df_dict:
                df_dict[json_file] = dict()
            df_dict[json_file] = dict(Counter(df_dict[json_file]) + Counter(dic))   # 既存の辞書と同じキーの要素を足す
    # この時点で、df辞書のマージ終わり(同じ単語の出現文書数を足し合わせた)

    c = 0
    for server, dic in df_dict.items():
        N = dic['NumOfPages']     # NumOfPageはそのサーバで辞書を更新した回数 = そのサーバのページ数
        if N == 0:
            continue
        idf_dict = dict()
        for word, count in dic.items():
            if not word == 'NumOfPages':
                idf = log(N / count) + 1
                idf_dict[word] = idf
        # 前回に出現していなかった単語のtf-idfを計算するためのidf値
        idf = log(N) + 1   # 初登場の単語になるので、countを1で計算
        idf_dict['NULLnullNULL'] = idf

        if idf_dict:
            f = open('../idf_dict/' + server, 'w')
            json.dump(idf_dict, f)
            f.close()
        c += 1
        print(str(c) + '/' + str(len(df_dict.keys())))
    os.chdir('../../')


def make_request_url_iframeSrc_set():
    try:
        os.mkdir('ROD/request_url')
    except FileExistsError:
        pass
    try:
        os.mkdir('ROD/iframe_src')
    except FileExistsError:
        pass
    lis = os.listdir('RAD/temp')
    for file in lis:
        with open('RAD/temp/' + file, 'rb') as f:
            pick = pickle.load(f)

        file = file[file.find('_') + 1:file.find('.')] + '.json'
        # ページをロードするために行ったrequestURLの集合を今までのデータとマージする
        if 'request' in pick and pick['request']:
            if os.path.exists('ROD/request_url/' + file):
                with open('ROD/request_url/' + file, 'r') as f:
                    url_set = set(json.load(f))
            else:
                url_set = set()
            url_set.update(pick['request'])
            with open('ROD/request_url/' + file, 'w') as f:
                json.dump(list(url_set), f)

        # iframeのsrc先URLの集合を今までのデータとマージする
        if 'iframe' in pick and pick['iframe']:
            if os.path.exists('ROD/iframe_src/' + file):
                with open('ROD/iframe_src/' + file, 'r') as f:
                    url_set = set(json.load(f))
            else:
                url_set = set()
            url_set.update(pick['iframe'])
            with open('ROD/iframe_src/' + file, 'w') as f:
                json.dump(list(url_set), f)

if __name__ == '__main__':
    make_and_save_host_idf_dict()     # 次回クローリングのためのidf値を計算する
    make_request_url_iframeSrc_set()  # 次回クローリングのための...
