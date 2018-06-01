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


def make_idf_dict_frequent_word_dict(org_path):
    df_dict = dict()   # {file名(server.json) : {単語:df値, 単語:df値, ...}, server : {df辞書}, ... , server : {df辞書} }
    if not os.path.exists(org_path + '/ROD/idf_dict'):
        os.mkdir(org_path + '/ROD/idf_dict')

    n = 100   # 頻出単語上位n個を保存
    if not os.path.exists(org_path + '/ROD/frequent_word_' + str(n)):
        os.mkdir(org_path + '/ROD/frequent_word_' + str(n))

    dir_list = os.listdir(org_path + '/ROD/df_dicts/')  # このフォルダ以下の全てのdfフォルダをマージしてidf辞書を作る
    for df_dict_dir in dir_list:
        pickle_file_list = os.listdir(org_path + '/ROD/df_dicts/' + df_dict_dir)
        for pickle_file in pickle_file_list:
            # 途中からpickleファイルに変更した
            with open(org_path + '/ROD/df_dicts/' + df_dict_dir + '/' + pickle_file, 'rb') as f:
                dic = pickle.load(f)   # df辞書ロード

            if len(dic) == 0:  # 中身がなければ次へ
                continue
            # df_dictはpickleファイルだが、頻出単語ファイルはjsonにするため
            file_name_json = pickle_file[0:pickle_file.find('.pickle')] + '.json'
            if file_name_json not in df_dict:
                df_dict[file_name_json] = dict()
            df_dict[file_name_json] = dict(Counter(df_dict[file_name_json]) + Counter(dic))   # 既存の辞書と同じキーの要素を足す
    # この時点で、df辞書のマージ終わり(同じ単語の出現文書数を足し合わせた)

    # 頻出単語辞書の作成
    for file_name, dic in df_dict.items():
        frequent_words = list()
        for word, df in sorted(dic.items(), key=lambda x: x[1], reverse=True):
            if word != 'NumOfPages':
                frequent_words.append(word)
            if len(frequent_words) == n:
                break
        with open(org_path + '/ROD/frequent_word_' + str(n) + '/' + file_name, 'w') as f:
            json.dump(frequent_words, f)

    # idf辞書の作成
    # 前回データからのみ
    pickle_files = os.listdir(org_path + '/RAD/df_dict')
    c = 0
    for pickle_file in pickle_files:

        idf_dict = dict()
        with open(org_path + '/RAD/df_dict/' + pickle_file, 'rb') as f:
            dic = pickle.load(f)
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
            # df_dictはpickleファイルだが、idfファイルはjsonにするため
            file_name_json = pickle_file[0:pickle_file.find('.pickle')] + '.json'
            with open(org_path + '/ROD/idf_dict/' + file_name_json, 'w') as f:
                json.dump(idf_dict, f)
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


def make_request_url_iframeSrc_link_host_set(org_path):
    if not os.path.exists(org_path + '/ROD/request_url'):
        os.mkdir(org_path + '/ROD/request_url')
    if not os.path.exists(org_path + '/ROD/iframe_src'):
        os.mkdir(org_path + '/ROD/iframe_src')
    if not os.path.exists(org_path + '/ROD/link_host'):
        os.mkdir(org_path + '/ROD/link_host')

    lis = os.listdir(org_path + '/RAD/temp')
    request_url = set()  # matome.jsonに保存する内容
    iframe_url = set()   # matome.jsonに保存する内容
    link_url = set()     # matome.jsonに保存する内容
    file_name_set = set()  # 今回のクローリングで見つからなかったサーバはtempになくてRODデータに保存されないので、それらもmatome.jsonにいれるため

    for file in lis:
        with open(org_path + '/RAD/temp/' + file, 'rb') as f:
            pick = pickle.load(f)
        file = file[file.find('_') + 1:file.find('.')] + '.json'
        file_name_set.add(file)

        # ネットワーク名 : URL = スキーマ(?) + ホスト部 + ネットワーク部 + ファイル位置　としたときの、ネットワーク部のところ

        # ページをロードするために行ったrequestURL(のネットワーク名)の集合を今までのデータとマージして、jsonとして保存
        if os.path.exists(org_path + '/ROD/request_url/' + file):
            with open(org_path + '/ROD/request_url/' + file, 'r') as f:
                url_set = set(json.load(f))
        else:
            url_set = set()
        if 'request' in pick and pick['request']:
            url_set.update(pick['request'])
        if url_set:
            request_url.update(url_set)
            with open(org_path + '/ROD/request_url/' + file, 'w') as f:
                json.dump(list(url_set), f)

        # iframeのsrc先URL(のネットワーク名)の集合を今までのデータとマージして、jsonとして保存
        if os.path.exists(org_path + '/ROD/iframe_src/' + file):
            with open(org_path + '/ROD/iframe_src/' + file, 'r') as f:
                url_set = set(json.load(f))
        else:
            url_set = set()
        if 'iframe' in pick and pick['iframe']:
            url_set.update(pick['iframe'])
        if url_set:
            iframe_url.update(url_set)
            with open(org_path + '/ROD/iframe_src/' + file, 'w') as f:
                json.dump(list(url_set), f)

        # リンクURL(のネットワーク名)の集合を今までのデータとマージして、jsonとして保存
        if os.path.exists(org_path + '/ROD/link_host/' + file):
            with open(org_path + '/ROD/link_host/' + file, 'r') as f:
                url_set = set(json.load(f))
        else:
            url_set = set()
        if 'link_host' in pick and pick['link_host']:
            url_set.update(pick['link_host'])
        if url_set:
            link_url.update(url_set)
            with open(org_path + '/ROD/link_host/' + file, 'w') as f:
                json.dump(list(url_set), f)

    # 今回見つからなかったが、過去に回ったことのあるサーバのRODデータをmatome.jsonに入れるためにそれぞれの集合に追加する
    # 上記の処理では、tempディレクトリを参考にしているため、今回のクローリングで見つからなかったサーバのデータは
    # それぞれの集合(request_urlとiframe_urlとlink_url)に入っていないため追加する
    if org_path == '../organization/立命館':
        file_name_set.add('falsification-cysec-cs-ritsumei-ac-jp.json')  # 偽サイト情報はmatome.jsonに入れない
    # request_url
    file_names = os.listdir(org_path + '/ROD/request_url')
    for file_name in file_names:
        # matome.jsonは参照しない
        if 'matome.json' in file_name:
            continue
        # matome.json以外で今回
        if file_name not in file_name_set:
            with open(org_path + '/ROD/request_url/' + file_name, 'r') as f:
                tmp = json.load(f)
            request_url.update(set(tmp))
    # iframe_src
    file_names = os.listdir(org_path + '/ROD/iframe_src')
    for file_name in file_names:
        if 'matome.json' in file_name:
            continue
        if file_name not in file_name_set:
            with open(org_path + '/ROD/iframe_src/' + file_name, 'r') as f:
                tmp = json.load(f)
            iframe_url.update(set(tmp))
    # link_host
    file_names = os.listdir(org_path + '/ROD/link_host')
    for file_name in file_names:
        if 'matome.json' in file_name:
            continue
        if file_name not in file_name_set:
            with open(org_path + '/ROD/link_host/' + file_name, 'r') as f:
                tmp = json.load(f)
            link_url.update(set(tmp))

    # 全サーバの情報をまとめた集合を保存、クローリング時にはこれを使う
    # このjsonファイルにないサーバ(ネットワーク)へ要求が出るものは、過去にはなかった通信になる
    with open(org_path + '/ROD/request_url/matome.json', 'w') as f:
        json.dump(list(request_url), f)
    with open(org_path + '/ROD/iframe_src/matome.json', 'w') as f:
        json.dump(list(iframe_url), f)
    with open(org_path + '/ROD/link_host/matome.json', 'w') as f:
        json.dump(list(link_url), f)


if __name__ == '__main__':
    make_idf_dict_frequent_word_dict()     # 次回クローリングのためのidf値を計算する
    make_request_url_iframeSrc_link_host_set()  # 次回クローリングのための...
