import os
import json
from math import log
import pickle

"""
クローリング後にサーバごとの
tf-idf値
ページのロードに行ったリクエストのURL集合
iframeのsrc先URLの集合
を保存する
"""
def make_and_save_host_idf_dict():
    try:
        os.mkdir('ROD/idf_dict')
    except FileExistsError:
        pass
    os.chdir('RAD/df_dict')
    lis = os.listdir()
    c = 0
    for server in lis:
        idf_dict = {}
        f = open(server, 'r')
        dic = json.load(f)
        f.close()
        if len(dic) == 0:
            continue
        N = dic['NumOfPages']     # NumOfPageはそのサーバで辞書を更新した回数 = そのサーバのページ数
        if N == 0:
            continue
        for word, count in dic.items():
            if not word == 'NumOfPages':
                idf = log(N / count) + 1
                idf_dict[word] = idf
        # 前回に出現していなかった単語のtf-idfを計算するためのidf値
        idf = log(N) + 1   # 初登場の単語になるので、countを1で計算
        idf_dict['NULLnullNULL'] = idf

        if not len(idf_dict) == 0:
            f = open('../../ROD/idf_dict/' + server, 'w')
            json.dump(idf_dict, f)
            f.close()
        c += 1
        print(str(c) + '/' + str(len(lis)))
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

        if pick[2]:
            file = file[file.find('_')+1:file.find('.')] + '.json'
            f = open('ROD/request_url/' + file, 'w')
            json.dump(list(pick[2]), f)
            f.close()
        if pick[3]:
            f = open('ROD/iframe_src/' + file, 'w')
            json.dump(list(pick[3]), f)
            f.close()

if __name__ == '__main__':
    make_and_save_host_idf_dict()
    make_request_url_iframeSrc_set()
