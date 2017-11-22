import os
import json
from math import log
import pickle
from collections import Counter
import shutil

"""
クローリング後にサーバごとの
tf-idf値
ページのロードに行ったリクエストのURL集合
iframeのsrc先URLの集合
をまとめて保存する
"""


def make_idf_dict_frequent_word_dict():
    df_dict = dict()   # {server : {単語:df値, 単語:df値, ...}, server : {df辞書}, ... , server : {df辞書} }
    try:
        os.mkdir('ROD/idf_dict')
    except FileExistsError:
        pass

    n = 100   # 頻出単語上位n個を保存
    try:
        os.mkdir('ROD/frequent_word_' + str(n))
    except FileExistsError:
        pass

    dir_list = os.listdir('ROD/df_dicts/')  # このフォルダ以下の全てのdfフォルダをマージしてidf辞書を作る
    for df_dict_dir in dir_list:
        json_file_list = os.listdir('ROD/df_dicts/' + df_dict_dir)
        for json_file in json_file_list:
            f = open('ROD/df_dicts/' + df_dict_dir + '/' + json_file, 'r')
            dic = json.load(f)   # df辞書ロード
            f.close()
            if len(dic) == 0:  # 中身がなければ次へ
                continue
            if json_file not in df_dict:
                df_dict[json_file] = dict()
            df_dict[json_file] = dict(Counter(df_dict[json_file]) + Counter(dic))   # 既存の辞書と同じキーの要素を足す
    # この時点で、df辞書のマージ終わり(同じ単語の出現文書数を足し合わせた)

    # 頻出単語辞書の作成
    for server, dic in df_dict.items():
        frequent_words = list()
        for word, df in sorted(dic.items(), key=lambda x: x[1], reverse=True):
            if word != 'NumOfPages':
                frequent_words.append(word)
            if len(frequent_words) == n:
                break
        with open('ROD/frequent_word_' + str(n) + '/' + server, 'w') as f:
            json.dump(frequent_words, f)

    # idf辞書の作成
    # 前回データからのみ
    lis = os.listdir('RAD/df_dict')
    c = 0
    for server in lis:
        idf_dict = dict()
        with open('RAD/df_dict/' + server, 'r') as f:
            dic = json.load(f)
        if len(dic) == 0:
            continue
        N = dic['NumOfPages']  # NumOfPageはそのサーバで辞書を更新した回数 = そのサーバのページ数
        if N == 0:
            continue
        for word, count in dic.items():
            if not word == 'NumOfPages':
                idf = log(N / count) + 1
                idf_dict[word] = idf
        # 前回に出現していなかった単語のtf-idfを計算するためのidf値
        idf = log(N) + 1  # 初登場の単語は、countを1でidf値を計算
        idf_dict['NULLnullNULL'] = idf

        if idf_dict:
            f = open('ROD/idf_dict/' + server, 'w')
            json.dump(idf_dict, f)
            f.close()
        c += 1
    """
    # 過去すべてのdfデータから計算
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
            f = open('ROD/idf_dict/' + server, 'w')
            json.dump(idf_dict, f)
            f.close()
        c += 1
    """


def make_request_url_iframeSrc_link_host_set():
    try:
        os.mkdir('ROD/request_url')
    except FileExistsError:
        pass
    try:
        os.mkdir('ROD/iframe_src')
    except FileExistsError:
        pass
    try:
        os.mkdir('ROD/link_host')
    except FileExistsError:
        pass

        """
    lis = os.listdir('ROD/link_host')
    for file in lis:
        url_domain_set = set()
        with open('ROD/link_host/' + file, 'r') as f:
            url_set = set(json.load(f))
        for url_domain in url_set:
            if url_domain.count('.') > 2:  # xx.ac.jpのように「.」が2つしかないものはそのまま
                url_domain = '.'.join(url_domain.split('.')[1:])  # www.ritsumei.ac.jpは、ritsumei.ac.jpにする
            url_domain_set.add(url_domain)
        with open('ROD/link_host/' + file, 'w') as f:
            json.dump(list(url_domain_set), f)

        """
    lis = os.listdir('RAD/temp')
    request_url = set()
    iframe_url = set()
    link_url = set()
    file_name_set = set()  # 今回のクローリングで見つからなかったサーバはtempにないため、RODデータに保存されないので、それを防ぐため
    for file in lis:
        with open('RAD/temp/' + file, 'rb') as f:
            pick = pickle.load(f)
        file = file[file.find('_') + 1:file.find('.')] + '.json'
        file_name_set.add(file)

        # ネットワーク名 : URL = ホスト部 + ネットワーク部 + ファイル位置　としたときの、ネットワーク部のところ

        # ページをロードするために行ったrequestURL(のネットワーク名)の集合を今までのデータとマージして、jsonとして保存
        if os.path.exists('ROD/request_url/' + file):
            with open('ROD/request_url/' + file, 'r') as f:
                url_set = set(json.load(f))
        else:
            url_set = set()
        if 'request' in pick and pick['request']:
            url_set.update(pick['request'])
        if url_set:
            request_url.update(url_set)
            with open('ROD/request_url/' + file, 'w') as f:
                json.dump(list(url_set), f)

        # iframeのsrc先URL(のネットワーク名)の集合を今までのデータとマージして、jsonとして保存
        if os.path.exists('ROD/iframe_src/' + file):
            with open('ROD/iframe_src/' + file, 'r') as f:
                url_set = set(json.load(f))
        else:
            url_set = set()
        if 'iframe' in pick and pick['iframe']:
            url_set.update(pick['iframe'])
        if url_set:
            iframe_url.update(url_set)
            with open('ROD/iframe_src/' + file, 'w') as f:
                json.dump(list(url_set), f)

        # リンクURL(のネットワーク名)の集合を今までのデータとマージして、jsonとして保存
        if os.path.exists('ROD/link_host/' + file):
            with open('ROD/link_host/' + file, 'r') as f:
                url_set = set(json.load(f))
        else:
            url_set = set()
        if 'link_host' in pick and pick['link_host']:
            url_set.update(pick['link_host'])
        if url_set:
            link_url.update(url_set)
            with open('ROD/link_host/' + file, 'w') as f:
                json.dump(list(url_set), f)

    # 今回見つからなかったが、過去に回ったことのあるサーバのRODデータをmatome.jsonに入れるため
    # request_url
    file_names = os.listdir('ROD/request_url')
    for file_name in file_names:
        if 'matome.json' in file_name:
            continue
        if file_name not in file_name_set:
            with open('ROD/request_url/' + file_name, 'r') as f:
                tmp = json.load(f)
            request_url.update(set(tmp))
    # iframe_src
    file_names = os.listdir('ROD/iframe_url')
    for file_name in file_names:
        if 'matome.json' in file_name:
            continue
        if file_name not in file_name_set:
            with open('ROD/iframe_url/' + file_name, 'r') as f:
                tmp = json.load(f)
            iframe_url.update(set(tmp))
    # link_host
    file_names = os.listdir('ROD/link_host')
    for file_name in file_names:
        if 'matome.json' in file_name:
            continue
        if file_name not in file_name_set:
            with open('ROD/link_host/' + file_name, 'r') as f:
                tmp = json.load(f)
            link_url.update(set(tmp))

    # 全サーバの情報をまとめた集合を保存、クローリング時にはこれを使う
    with open('ROD/request_url/matome.json', 'w') as f:
        json.dump(list(request_url), f)
    with open('ROD/iframe_src/matome.json', 'w') as f:
        json.dump(list(iframe_url), f)
    with open('ROD/link_host/matome.json', 'w') as f:
        json.dump(list(link_url), f)


if __name__ == '__main__':
    make_idf_dict_frequent_word_dict()     # 次回クローリングのためのidf値を計算する
    make_request_url_iframeSrc_link_host_set()  # 次回クローリングのための...
