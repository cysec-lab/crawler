from __future__ import annotations

import json
import os
import pickle
from collections import Counter
from logging import getLogger
from math import log
from multiprocessing import Queue
from typing import Any, Dict
from urllib.parse import urlparse

from utils.file_rw import r_file
from utils.logger import worker_configurer

request_url = set()  # matome.jsonに保存する内容
iframe_url = set()   # グローバル変数にしておかないと、exec()関数内で更新できない
link_url = set()
script_url = set()

logger = getLogger(__name__)


def make_idf_dict_frequent_word_dict(queue_log: Queue[Any],org_path: str):
    """
    クローリング後にサーバごとの
    tf-idf値
    ページのロードに行ったリクエストのURL集合
    iframeのsrc先URLの集合
    をまとめて保存する
    また、リンク、リクエストURLの既知サーバを示すホワイトリストのフィルタを作成する
    """
    worker_configurer(queue_log, logger)
    df_dict: Dict[str, Dict[str, Any]] = dict()   # {file名(server.json) : {単語:df値, 単語:df値, ...}, server : {df辞書}, ... , server : {df辞書} }
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
        frequent_words: list[str] = list()
        for word, _ in sorted(dic.items(), key=lambda x: x[1], reverse=True):
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

        idf_dict: Dict[str, float] = dict()
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


def make_filter(org_path: str):
    """
    alertdirの link_to_new_server.csv と new_request_url.csv から フィルタを作る
    フィルタは alert に記録されたURLのホスト名から作る (パスの途中まで設定できるようになっているが、その調整は手動でする)
    作ったフィルタは org_path/ に保存
    """
    obj_list = ["link", "request"]

    for obj in obj_list:
        new_url_set = set()
        new_url_filter: Dict[str, list[str]] = dict()

        # ファイルロード
        if os.path.exists("{}/alert/{}_to_new_server.csv".format(org_path, obj)):
            new_url_file = r_file(name="{}/alert/{}_to_new_server.csv".format(org_path, obj))
            # 4列目以降のデータを集合に追加
            for line in new_url_file.splitlines()[1:]:  # [1:]でヘッダを飛ばす
                new_url_set = new_url_set.union(line.split(",")[3:])

        # 新しいフィルタを作成 フィルタ-> {ホスト名: "", ホスト名: "", ...}
        if new_url_set:
            new_url_host_set = set([urlparse(url[1:-1]).netloc for url in new_url_set])  # [1:-1]でjsonの文字列を表す「'」を消す
            new_url_host_set.discard("192.168.0.233")  # 研究室内の偽サーバの情報は削除(別アラートファイルに保存するようにしたので、もういらない)
            new_url_filter = {host: [""] for host in new_url_host_set if host}

        # jsonとして保存
        with open("{}/new_{}_filter.json".format(org_path, obj), "w") as f:
            json.dump(new_url_filter, f)


def merge_filter(org_path: str):
    obj_list = ["link", "request"]
    temp_dict: Dict[str, Dict[str, Any]] = dict()

    # link と request の文字部分以外は処理が同じなので、 for文でまとめる
    for obj in obj_list:
        # 必要なdirがなければ作成
        if not os.path.exists("{}/ROD/{}_url".format(org_path, obj)):
            os.mkdir("{}/ROD/{}_url".format(org_path, obj))

        # 既存のフィルタロード
        if os.path.exists("{}/ROD/{}_url/filter.json".format(org_path, obj)):
            with open("{}/ROD/{}_url/filter.json".format(org_path, obj)) as f:
                temp_dict["old_{}_filter".format(obj)] = json.load(f)
        else:
            temp_dict["old_{}_filter".format(obj)] = dict()

        # 新しいフィルタロード
        if os.path.exists("{}/new_{}_filter.json".format(org_path, obj)):
            with open("{}/new_{}_filter.json".format(org_path, obj)) as f:
                temp_dict["new_{}_filter".format(obj)] = json.load(f)
        else:
            temp_dict["new_{}_filter".format(obj)] = dict()

        # 新しいフィルタを古いフィルタにマージ (同じホスト名があった場合は、valueのリストを連結
        for key, value in temp_dict["new_{}_filter".format(obj)].items():
            if key in temp_dict["old_{}_filter".format(obj)]:
                if value[0]:  # ひとつ目が空文字じゃなければ
                    temp_dict["old_{}_filter".format(obj)][key].extend(value)
            else:
                temp_dict["old_{}_filter".format(obj)][key] = value

        # 保存
        with open("{}/ROD/{}_url/filter.json".format(org_path, obj), "w") as f:
            json.dump(temp_dict["old_{}_filter".format(obj)], f)


def make_request_url_iframeSrc_link_host_set(queue_log: Queue[Any], org_path: str):
    """
    1. lis = RAD/tempの中のpickleファイルを順番に開いていく(ファイルの中身は辞書)
    2. url_set = 過去のデータ(ROD/[object]_url/ホスト名.json)のファイルを開く
    3. 辞書から特定のkey(object_list)のデータを取得
    4. それぞれのデータ(pick[obj])を過去(ROD)のデータ(url_set)とマージする
    5. マージしたデータ(url_set)を ROD/[object]_url/ホスト名.json に保存
    """
    worker_configurer(queue_log, logger)
    object_list = ['request', 'iframe', 'link', 'script']

    # RODに保存dirがなければ作る
    for obj in object_list:
        if not os.path.exists(org_path + '/ROD/' + obj + '_url'):
            os.mkdir(org_path + '/ROD/' + obj + '_url')

    # 今回のクローリングで集めたデータのpickleファイルのリストを取得
    lis = os.listdir(org_path + '/RAD/temp')
    global request_url, iframe_url, link_url, script_url   # global変数じゃないとexec関数で未定義のエラーが出る(たしか
    file_name_set = set()  # .pickleを.jsonに名前変更した集合

    for file in lis:
        # 1.
        with open(org_path + '/RAD/temp/' + file, 'rb') as f:
            pick = pickle.load(f)
        file = file[file.find('_') + 1:file.find('.')] + '.json'
        file_name_set.add(file)

        # それぞれのデータを過去のデータとマージしてjsonで保存
        for obj in object_list:
            # 2.
            if os.path.exists(org_path + '/ROD/' + obj + '_url/' + file):
                with open(org_path + '/ROD/' + obj + '_url/' + file, 'r') as f:
                    url_set = set(json.load(f))
            else:
                url_set = set()
            # 3. 4.
            if obj in pick and pick[obj]:
                url_set.update(pick[obj])
            # 5.
            if url_set:
                exec(obj + "_url.update(url_set)")
                with open(org_path + '/ROD/' + obj + '_url/' + file, 'w') as f:
                    json.dump(list(url_set), f)

    # 今回見つからなかったが、過去に回ったことのあるサーバのRODデータをmatome.jsonに入れるためにそれぞれの集合に追加する
    # 上記の処理では、tempディレクトリを参考にしているため、今回のクローリングで見つからなかったサーバのデータは
    # それぞれの集合(request_urlとiframe_urlとlink_url)に入っていないため、過去の情報を追加する
    if '/organization/ritsumeikan' in org_path:
        file_name_set.add('falsification-cysec-cs-ritsumei-ac-jp.json')  # 偽サイト情報はmatome.jsonに入れない

    # ROD/request, iframe, script, linkの各JSONデータをmatome.jsonとしてまとめる
    for obj in object_list:
        file_names = os.listdir(org_path + '/ROD/' + obj + '_url')
        for file_name in file_names:
            # matome.jsonは参照しない(RODには前回使ったmatome.jsonがあるのでそれは無視)
            if 'matome.json' in file_name:
                continue
            # matome.json以外で、過去に見つけていたが今回見つからなかったサーバの情報を追加
            # TODO: 未完成のところ
            if file_name not in file_name_set:
                with open(org_path + '/ROD/' + obj + '_url/' + file_name, 'r') as f:
                    tmp = json.load(f) # type: ignore
                    try:
                        exec(obj + "_url.update(set(tmp))")
                    except Exception as err:
                        logger.exception(f'{err}')
        # 全サーバの情報をまとめた集合を保存、クローリング時にはこれを使う
        with open(org_path + '/ROD/' + obj + '_url/matome.json', 'w') as f:
            try:
                exec("json.dump(list(" + obj + "_url), f)")
            except Exception as err:
                logger.exception(f'{err}')
