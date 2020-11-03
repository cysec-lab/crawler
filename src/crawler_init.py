from __future__ import annotations

import datetime
import dbm
import json
import os
import pickle
from collections import deque
from logging import getLogger
from multiprocessing import Process, Queue, cpu_count
from shutil import copyfile, copytree
from time import sleep, time
from typing import Any, Deque, Dict, List, Tuple, Union, cast
from urllib.parse import urlparse

from clamd import clamd_main
from crawler import crawler_main
from file_rw import r_file, r_json, w_file, w_json
from logger import worker_configurer
from resources_observer import MemoryObserverThread
from summarize_alert import summarize_alert_main

logger = getLogger(__name__)

# 接続すべきURLかどうか判断するのに必要なリストをまとめた辞書
filtering_dict: Dict[str, Dict[str, Union[str, int, None, Dict[str, Dict[str, List[str]]]]]] = dict()
clamd_q: Dict[str, Union[Queue[str], Process]] = dict()
summarize_alert_q: Dict[str, Any] = dict()

# これらホスト名辞書はまとめてもいいが、まとめるとどこで何を使ってるか分かりにくくなる
# ホスト名 : {"URL_list": 待機URLのリスト[(deque)], "update_time": リストからURLをpopした時の時間int}
# Dict[str, Union[Dict[str, Union[str, deque[Tuple[str, ...]]]], int, Any]]
hostName_remaining: Dict[str, Dict[str, Any]] = dict()
hostName_achievement: Dict[str, int] = dict()   # ホスト名 : 達成数

# 以下の三つはkeyの作成、削除タイミングが同じ
hostName_process: Dict[str, Process] = dict()   # ホスト名 : 子プロセス
hostName_queue: Dict[str, Any] = dict()         # ホスト名 : 通信キュー
hostName_args: Dict[str, Any] = dict()          # ホスト名 : 子プロセスの引数
fewest_host = None                              # 待機URL数が一番少ないホスト名

url_db = None               # key-valueデータベース. URL : (True or False or Black or Unknown or Special) + , +  nth
nth: Union[int, str] = 0    # 何回目のクローリングか
org_path: str = ""          # 組織ごとのディレクトリの絶対パス  /home/ユーザ名/.../organization/組織名

url_list: Deque[Tuple[str, ...]] = deque()  # (URL, リンク元)のタプルのリスト(子プロセスに送信用)
assignment_url_set = set()                  # 割り当て済みのURLの集合
remaining = 0                               # 途中保存で終わったときの残りURL数
send_num = 0                                # 途中経過で表示する5秒ごとの子プロセスに送ったURL数
recv_num = 0                                # 途中経過で表示する5秒ごとの子プロセスから受け取ったURL数
all_achievement: int = 0

def get_setting_dict(path: str) -> dict[str, Union[str, bool, int, None]]:
    """
    設定ファイルの読み込み
    args:
        path: 設定ファイルまでのパス(.../crawler/organization/<hoge>/ROD/LIST)
    return:
        setting dict: 設定が書かれた辞書型
    """

    setting: dict[str, Union[str, int, bool, None]] = dict()
    bool_variable_list = ['assignOrAchievement', 'screenshots', 'clamd_scan', 'headless_browser', 'mecab']
    setting_file = r_file(path + '/SETTING.txt')
    setting_line = setting_file.split('\n')

    # 設定ファイルを1行づつ読む
    for line in setting_line:
        if line and not line.startswith('#'):
            # 左変
            variable = line[0:line.find('=')]
            # 右辺
            right_side = line[line.find('=')+1:]

            if variable == 'MAX_page':
                try:
                    value = int(right_side) # 文字(小数点も)をはじく.でも空白ははじかないみたい
                except ValueError:
                    logger.warning("couldn't import setting file. Invalid value 'MAX_page'")
                    setting['MAX_page'] = None
                else:
                    setting['MAX_page'] = value

            elif variable == 'MAX_time':
                # MAX_timeは60秒*5のように指定できる
                right_side_split = right_side.split('*')
                value = 1
                try:
                    for i in right_side_split:
                        value *= int(i)
                except ValueError:
                    logger.warning("couldn't import setting file. Invalid value 'MAX_time'")
                    setting['MAX_time'] = None
                else:
                    setting['MAX_time'] = value

            elif variable == 'SAVE_time':
                # SAVE_timeは60秒*5のように指定できる
                right_side_split = right_side.split('*')
                value = 1
                try:
                    for i in right_side_split:
                        value *= int(i)
                except ValueError:
                    logger.warning("couldn't import setting file. Invalid value 'SAVE_time'")
                    setting['SAVE_time'] = None
                else:
                    setting['SAVE_time'] = value

            elif variable == 'run_count':
                # 今何回目の実行かを設定
                try:
                    value = int(right_side)
                except ValueError:
                    logger.error("couldn't import setting file. Invalid value 'run_count'")
                    setting['run_count'] = None
                else:
                    setting['run_count'] = value

            elif variable == 'MAX_process':
                # 各サーバを担当する子プロセスの最大作成数
                try:
                    value = int(right_side)
                except ValueError:
                    logger.warning("couldn't import setting file. Invalid value 'MAX_process'")
                    setting['MAX_process'] = None
                else:
                    if value == 0:
                        # 0は論理プロセッサ数を使用
                        setting['MAX_process'] = cpu_count()
                    elif value < 0:
                        # 負数は論理プロセッサ数から引く
                        setting['MAX_process'] = cpu_count() + value if cpu_count() + value > 0 else 1
                    else:
                        setting['MAX_process'] = value

            elif variable in bool_variable_list:
                # True or Falseの2値しか取らない設定をまとめて調べる
                if right_side == 'True':
                    setting[variable] = True
                elif right_side == 'False':
                    setting[variable] = False
                else:
                    logger.warning("couldn't import setting file. Invalid value '%s'", variable)
                    setting[variable] = False

            else:
                # 知らない設定コマンドが存在した場合
                logger.warning("couldn't import setting file. Extra setting exist. What's '%s'", variable)
                setting['extra'] = None

    logger.debug('Get Setting Dict Fin!')
    return setting


def import_file(path: str):
    """
    フィルタ設定ファイルたちが存在すればインポート
    接続すべきURLかどうか判断するfiltering_dictを作成する
    args:
        path: 設定ファイルまでのパス(.../crawler/organization/<hoge>/ROD/LIST)
    """

    filter_list = ["DOMAIN", "WHITE", "IPAddress", "REDIRECT", "BLACK"]
    for filter_ in filter_list:
        if os.path.exists("{}/{}.json".format(path, filter_)):
            with open("{}/{}.json".format(path, filter_), "r") as f:
                filtering_dict[filter_] = json.load(f)
        else:
            filtering_dict[filter_] = dict()
    logger.debug('Import Setting filters Fin!')


def make_dir(screenshots: bool):
    """
    必要なディレクトリが存在しなければ作成する.
    実行ディレクトリは ".../crawler/organization/'hoge'"
    引数がTrueならば screenshots を保存するディレクトリも作る
    - /ROD/
        - 過去のデータなど. クローリング時に参照するデータ.
    - /RAD/
        - 今回集めたデータを保存するディレクトリ
        - このデータは次回以降のクローリングで使用する. クローリング中に更新.
    - /result/
        - 今回のクローリング結果を保存するディレクトリ
    args:
        screenshot bool: スクリーンショットを撮る場合には保存用ディレクトリを作成
    """

    dir_list = ["/ROD/url_hash_json", "/ROD/tag_data", "/ROD/df_dicts",
                    "/RAD/df_dict", "/RAD/temp", "/result"]

    for dir_name in dir_list:
        if not os.path.exists(org_path + dir_name):
            os.mkdir(org_path + dir_name)
    if screenshots:
        if not os.path.exists(org_path + '/RAD/screenshots'):
            os.mkdir(org_path + '/RAD/screenshots')
    logger.debug('Make save Dirs Fin!')


def init(queue_log: Queue[Any], process_run_count: int, setting_dict: dict[str, Union[str, int, bool, None]]):
    """
    初期設定
    実行ディレクトリは「result」, 最後の方に「result_*」に移動
    /RAD/url_db (dbm Moudle)の作成
    args:
        process_run_count: クローラの実行回数, 初回実行の場合処理が変化
        setting_dict: SETTING.txtに書いた設定たちをまとめた辞書
    return:
        bool: 初期設定のなにかしらで失敗するとFalse, 成功すればTrue
    """

    # url_dbの作成
    global url_db
    url_db = dbm.open(org_path + '/RAD/url_db', 'c')

    clamd_scan = setting_dict['clamd_scan']
    # machine_learning_ = setting_dict['machine_learning']
    # screenshots_svc = setting_dict['screenshots_svc']

    # 検索済みURL, 検索待ちURLなど, 途中保存データを読み込む
    global all_achievement
    if process_run_count == 0:
        # 初回実行の場合は, START_LIST.txt だけ読み込む
        data_temp_startlist: str = r_file(org_path + '/ROD/LIST/START_LIST.txt')
        data_temp_startlist_split: List[str] = data_temp_startlist.split('\n')
        url_list.extend([(ini, "START") for ini in data_temp_startlist_split if ini])

    else:
        # 2回め以降の実行ならresultからデータを読み出す
        if not os.path.exists('result_' + str(process_run_count)):
            logger.error('result_%d which the result of last crawling is not found.', process_run_count)
            return False
        # 総達成数
        data_all_achievement: int = r_json('result_' + str(process_run_count) + '/all_achievement')
        all_achievement = data_all_achievement

        # 子プロセスに割り当てたURLの集合
        data_assignment_url_set = r_json('result_' + str(process_run_count) + '/assignment_url_set')
        assignment_url_set.update(set(data_assignment_url_set))

        # ホスト名を見て分類する前のリスト
        data_utl_list: List[List[str]] = r_json('result_' + str(process_run_count) + '/url_list')
        url_list.extend([tuple(i) for i in data_utl_list])

        # 各ホストごとに分類されたURLの辞書
        with open('result_' + str(process_run_count) + '/host_remaining.pickle', 'rb') as f:
            data_temp = pickle.load(f)
        hostName_remaining.update(data_temp)
        for host_name in hostName_remaining.keys():
            hostName_remaining[host_name]["update_time"] = 0

    # 作業ディレクトリを作って移動
    try:
        os.mkdir('result_' + str(process_run_count + 1))
        os.chdir('result_' + str(process_run_count + 1))
    except FileExistsError:
        logger.error('init : result_%d directory has already made.', process_run_count + 1)
        return False

    # summarize_alertのプロセスを起動
    recvq: Queue[str] = Queue()
    sendq: Queue[str] = Queue()
    summarize_alert_q['recv'] = recvq  # 子プロセスが受け取る用のキュー
    summarize_alert_q['send'] = sendq  # 子プロセスから送信する用のキュー
    p = Process(target=summarize_alert_main, args=(queue_log, recvq, sendq, nth, org_path))
    p.daemon = True
    p.start()
    summarize_alert_q['process'] = p

    # clamdを使うためのプロセスを起動(その子プロセスでclamdを起動)
    if clamd_scan:
        recvq: Queue[str] = Queue()
        sendq: Queue[str] = Queue()
        clamd_q['recv'] = recvq   # clamdプロセスが受け取る用のキュー
        clamd_q['send'] = sendq   # clamdプロセスから送信する用のキュー
        p = Process(target=clamd_main, args=(queue_log, recvq, sendq, org_path))
        p.daemon = True
        p.start()
        clamd_q['process'] = p
        # clamdへの接続
        if sendq.get(block=True):
            # 成功
            logger.info('connect to clamd')
        else:
            # 失敗ならばFalseを返す
            logger.error('Fail to connect Clamd')
            return False

    # if machine_learning_:
    #     """
    #     # 機械学習を使うためのプロセスを起動
    #     recvq = Queue()
    #     sendq = Queue()
    #     machine_learning_q['recv'] = recvq
    #     machine_learning_q['send'] = sendq
    #     p = Process(target=machine_learning_main, args=(recvq, sendq, '../../ROD/tag_data'))
    #     p.start()
    #     machine_learning_q['process'] = p
    #     print('main : wait for machine learning...')
    #     print(sendq.get(block=True))   # 学習が終わるのを待つ(数分？)
    #     """
    #     print("main : cant use machine-learning.")
    #     return False
    # if screenshots_svc:
    #     """
    #     # 機械学習を使うためのプロセスを起動
    #     recvq = Queue()
    #     sendq = Queue()
    #     screenshots_svc_q['recv'] = recvq
    #     screenshots_svc_q['send'] = sendq
    #     p = Process(target=screenshots_learning_main, args=(recvq, sendq, '../../ROD/screenshots'))
    #     p.start()
    #     screenshots_svc_q['process'] = p
    #     print('main : wait for screenshots learning...')
    #     print(sendq.get(block=True))   # 学習が終わるのを待つ(数分？)
    #     """
    #     print("main : cant use screenshots-svc.")
    #     return False
    return True


def get_alive_child_num() -> int:
    """
    クローリング子プロセスの中で生きている数を返す
    return:
        count: 子プロセスの数
    """
    count = 0
    for host_temp in hostName_process.values():
        if host_temp.is_alive():
            count += 1
    return count


def get_achievement_amount()-> int:
    """
    各子プロセスから集約した達成数を返す
    達成数 = ページ数(リンク集が返ってきた数) + ファイル数(ファイルの達成通知の数)
    return:
        achievement int: 達成数
    """

    achievement: int = 0
    for achievement_num in hostName_achievement.values():
        achievement += achievement_num
    return achievement


def print_progress(run_time_pp: int, current_achievement: int):
    """
    10秒ごとにmainループから呼び出されて途中経過を表示する
    メインループが動いてることを確認するためにスレッド化していない
    args:
        run_time_pp: 現在時刻 - 開始時刻
        current_achievement: 現在の検査終了ページ数
    """

    global send_num, recv_num, all_achievement
    alive_count = get_alive_child_num()

    count = 0
    for _, remaining_dict in hostName_remaining.items():
        remaining_num = len(remaining_dict['URL_list'])

        # URL待機リストが空のホスト数をカウント
        if remaining_num == 0:
            count += 1
        else:
            pass
            # if host in hostName_process:
            #     print('main : ' + host + "'s remaining is " + str(remaining_num) +
            #           '\t active = ' + str(hostName_process[host].is_alive()))
            # else:
            #     print('main : ' + host + "'s remaining is " + str(remaining_num) + "\t active = isn't made")

    logger.info(f"""
    ---------progress--------
    remain host      = {count}
    run time         = {run_time_pp}
    recv:send URL    = {recv_num} : {send_num}
    achieve/assign   = {current_achievement} / {len(assignment_url_set)}
    all achivement   = {all_achievement + current_achievement}
    alive child proc = {alive_count}
    remaining        = {remaining}
    -------------------------""")
    send_num = 0
    recv_num = 0


def forced_termination():
    """
    強制終了させるために途中経過を保存する
    """
    global all_achievement
    logger.info("Forced terminate")

    # 子プロセスがなくなるまで回り続ける
    while get_alive_child_num() > 0:
        # 子プロセスからのデータを抜き取る
        receive_and_send(not_send=True)
        for host_name, host_name_remaining in hostName_remaining.items():
            length = len(host_name_remaining['URL_list'])
            if length:
                logger.info("%s: remaining -> %d", host_name, length)
        logger.info("wait for finishing alive process: %d", get_alive_child_num())
        del_child(int(time()))
        sleep(3)

    # 続きをするために途中経過を保存する
    all_achievement += get_achievement_amount()
    w_json(name='url_list', data=list(url_list))
    w_json(name='assignment_url_set', data=list(assignment_url_set))
    w_json(name='all_achievement', data=all_achievement)
    with open('host_remaining.pickle', 'wb') as f:
        pickle.dump(hostName_remaining, f)

    logger.info("Forced terminated")


def end():
    """
    終了判定
    全ての待機キューにURLがなく, 全ての子プロセスが終了していたらTrue
    """

    # 子プロセスに送るためのURLのリストが空
    if url_list:
        return False

    # 生きている子プロセスがいる
    if get_alive_child_num():
        return False

    # キューに要素があるか
    for _, remaining_temp in hostName_remaining.items():
        remaining_temp = cast(Dict[str, deque[Tuple[str]]], remaining_temp)
        if len(remaining_temp['URL_list']):
            return False

    # すべてなければ晴れて終了
    return True


def make_process(host_name: str, queue_log: Queue[Any], setting_dict: dict[str, Union[str, bool, int, None]]):
    """
    クローリングプロセスの生成
    すでに一度作ったことがあるならばプロセスを生成するのみ
    args:
        host_name: 
        setting_dict: 
    """

    if host_name not in hostName_process:
        # まだ一度もプロセスを作ったことのないホストに対して、プロセス作成

        # 子プロセスと通信するキュー
        child_sendq: Queue[str] = Queue()
        parent_sendq: Queue[str] = Queue()

        # 子プロセスに渡す引数辞書
        args_dic: dict[str, Union[str, int, Queue[str], bool, Process, Queue[Dict[str, str]], Dict[str, str], Dict[str, List[str]]]] = dict()
        args_dic['host_name'] = host_name                       # ホスト名
        args_dic['parent_sendq'] = parent_sendq                 # 通信用キュー
        args_dic['child_sendq'] = child_sendq                   # 通信用キュー
        args_dic['alert_process_q'] = summarize_alert_q['recv'] # 通信用キュー(警告文等)
        if setting_dict['clamd_scan']:                          # Clamdチェックするか否か
            args_dic['clamd_q'] = clamd_q['recv']
        else:
            args_dic['clamd_q'] = False
        # if setting_dict['machine_learning']:
        #     args_dic['machine_learning_q'] = machine_learning_q['recv']
        # else:
        #     args_dic['machine_learning_q'] = False
        # if setting_dict['screenshots_svc']:
        #     args_dic['screenshots_svc_q'] = screenshots_svc_q['recv']
        # else:
        #     args_dic['screenshots_svc_q'] = False

        args_dic['nth'] = cast(int, nth)
        args_dic['headless_browser'] = cast(bool, setting_dict['headless_browser'])
        args_dic['mecab'] = cast(bool, setting_dict['mecab'])               # Mecabを利用するか否か
        args_dic['screenshots'] = cast(bool, setting_dict['screenshots'])   # スクリーンショットを撮るか否か
        args_dic['org_path'] = org_path
        args_dic["filtering_dict"] = cast(Dict[str, List[str]], filtering_dict)

        # クローリングプロセスの引数は、サーバ毎に毎回同じ
        # hostName_args[]に設定を保存しておく
        hostName_args[host_name] = args_dic

        # プロセス作成
        try:
            p = Process(target=crawler_main, name=host_name, args=(queue_log, hostName_args[host_name], ))
            p.daemon = True # 親が死ぬと子も死ぬ
            p.start()       # スタート
        except Exception as err:
            logger.exception(f'{err}')

        # クローリングプロセスのpidを保存
        hostName_process[host_name] = p
        # クローリングプロセスとの通信用キューを記録
        hostName_queue[host_name] = {'child_send': child_sendq, 'parent_send': parent_sendq}

        # 初めて探索されるホスト名ならば
        if host_name not in hostName_achievement:
            # ホスト到達回数を0
            hostName_achievement[host_name] = 0

        # プロセス開始通知
        if p.pid:
            logger.info("%s's process start(pid=%d)", host_name, p.pid)
        else:
            logger.warning("Try to start %s's process, but pid is None", host_name)

    else:
        # 一度プロセスを作ったことのあるホストに対して
        # すでに保存されていたpidの削除
        del hostName_process[host_name]
        logger.info("%s is not alive", host_name)

        # 新規のプロセス作成
        p = Process(target=crawler_main, name=host_name, args=(queue_log, hostName_args[host_name],))
        p.daemon = True # 親が死ぬと子も死ぬ
        p.start()       # スタート
        hostName_process[host_name] = p # プロセスpidを指す辞書を更新する
        logger.info("%s's process start(pid=%d)", host_name, p.pid)


def receive_and_send(not_send: bool=False):
    """
    子プロセスからの情報を受信する、plzを受け取るとURLを子プロセスに送信する
    受信したリスト:
        辞書、タプル、文字列の3種類
        - {'type': '文字列', 'url_set': [(url, 検査結果), (url, 検査結果),...], "url_src": URLが貼ってあったページURL, オプション}
          - links: ページクローリング結果
          - file_done: ファイルクローリング結果
          - new_window_url: 新しい窓(or tab)に出たURL
          - redirect: ホワイトリストになければアラートを発する
        - (url, 'redirect')
          - リダイレクトが起こったが、ホスト名が変わらず、そのまま子プロセスで処理続行した
        - "receive"
          - 子プロセスがURLのタプルを受け取るたびに送信する
        - "plz"
          - 子プロセスがURLのタプルを要求
        クローリングするURLならばurl_listに追加
    args:
        not_send: Trueならば子プロセスにURLを送信しない
                  子プロセスからのデータを受け取りたいだけの時に利用
    """
    global recv_num, send_num

    # 通信用キューをループで回る
    for host_name, queue in hostName_queue.items():
        try:
            received_data = queue['child_send'].get(block=False)
        except Exception:
            # queueにデータがなければエラーが出る
            continue

        if type(received_data) is str:
            # 子プロセスから文字列を受け取った
            if received_data == 'plz':
                # 子プロセスからのメッセージがURLの送信要求の場合
                hostName_remaining[host_name]['update_time'] = int(time())
                if not_send is True:
                    queue['parent_send'].put('nothing')
                else:
                    if hostName_remaining[host_name]['URL_list']:
                        # クローリング対象URLが残っていればクローリングするurlを送信
                        remain = cast(deque[str], hostName_remaining[host_name]['URL_list'])
                        while True:
                            url_tuple: str = remain.popleft()
                            if url_tuple[0] not in assignment_url_set:
                                # まだ送信していないURLならばURLを送信してBreak
                                assignment_url_set.add(url_tuple[0])
                                queue['parent_send'].put(url_tuple)
                                send_num += 1
                                break
                            if not hostName_remaining[host_name]['URL_list']:
                                # 待機リストが空ならば子プロセスにもうURLがないことを伝えてbreak
                                queue['parent_send'].put('nothing')
                                break
                    else:
                        # クローリング対象URLがもうないのならば終了を伝える
                        queue['parent_send'].put('nothing')

        elif type(received_data) is tuple:
            # 子プロセスからタプルを渡された
            # (リダイレクトしたが、ホスト名が変わらなかったため子プロセスで処理を続行した)
            # リダイレクト後のURLを割り当て済みURLに追加
            assignment_url_set.add(received_data[0])
            url_db[received_data[0]] = 'True,' + str(nth)

        elif type(received_data) is dict:
            # 辞書型が子プロセスからきた
            url_tuple_set = set()
            url_src = "NONE"

            if "url_set" in received_data:
                # [(url, 検査結果), (url, 検査結果),...]
                url_tuple_set = received_data["url_set"]
            if "url_src" in received_data:
                # URLが貼ってあったページURL
                url_src = received_data["url_src"]

            # Type(文字列)の処理
            if received_data['type'] == 'links':
                # ページクローリング結果なので、検索済み数更新
                hostName_achievement[host_name] += 1
            elif received_data['type'] == 'file_done':
                # ファイルクローリング結果なので、検索済み数更新して次へ
                hostName_achievement[host_name] += 1
                continue
            elif received_data['type'] == 'new_window_url':
                # 新しい窓(orタブ)に出たURL(今のところ見つかってない)
                for url_tuple in url_tuple_set:
                    data_temp = dict()
                    data_temp['url'] = url_tuple[0]
                    data_temp['src'] = url_src
                    data_temp['file_name'] = 'new_window_url.csv'
                    data_temp['content'] = url_tuple[0] + ',' + url_src
                    data_temp['label'] = 'NEW_WINDOW_URL,URL'
                    summarize_alert_q['recv'].put(data_temp)
            elif received_data['type'] == 'redirect':
                # リダイレクトの場合、URLがホワイトリストにかからなければアラート
                # リダイレクトの場合、url_tuple_setの要素は1個(リダイレクト先)だけ
                url, check_result = list(url_tuple_set)[0]
                if (check_result is False) or (check_result == "Unknown"):
                    # リダイレクト先を調べる
                    redirect_host: str = urlparse(url).netloc
                    redirect_path: str = urlparse(url).path
                    w_alert_flag = True

                    # ホスト名+パスの途中までを見てホワイトリストに引っかかるか
                    filering_dictionaly= cast(Dict[str, Dict[str, List[str]]], filtering_dict["REDIRECT"]["allow"])
                    for white_host, white_path_list in filering_dictionaly.items():
                        if redirect_host.endswith(white_host) and \
                                [wh_pa for wh_pa in white_path_list if redirect_path.startswith(wh_pa)]:
                            # ホワイトリスト内にリダイレクト先が存在するならアラート撤回
                            w_alert_flag = False
                            break

                    #######################################
                    # ToDo: Ifいらないと思う
                    if w_alert_flag:
                        data_temp: dict[str, str] = dict()
                        data_temp['url'] = url
                        data_temp['src'] = url_src
                        data_temp['file_name'] = 'after_redirect_check.csv'
                        data_temp['content'] = received_data["ini_url"] + ',' + url_src + ',' + url
                        data_temp['label'] = 'URL,SOURCE,REDIRECT_URL'
                        summarize_alert_q['recv'].put(data_temp)
                    ########################################

                # リダイレクト状況を保存(after_redirect.csv)する
                # (リダイレクト前URL, リダイレクト前URLのsrcURL, リダイレクト後URL, リダイレクト後URLの判定結果)
                w_file('after_redirect.csv', received_data["ini_url"] + ',' + received_data["url_src"] + ',' +
                       url + "," + str(check_result) + '\n', mode="a")

            # リンクやnew_window_url, リダイレクト先をurlリストに追加
            # 既に割り当て済みの場合は追加しない
            if url_tuple_set:
                recv_num += len(url_tuple_set)
                # 接続診断結果がTrueのURLをurl_listに追加
                for url_tuple in url_tuple_set:
                    if url_tuple[1] is True:
                        # 分類待ちリストに入れる
                        url_list.append((url_tuple[0], url_src))
                    # url_dbの更新
                    url_db[url_tuple[0]] = str(url_tuple[1]) + ',' + str(nth)


def allocate_to_host_remaining(url_tuple: Tuple[str, ...]):
    """
    url_tupleの中にあるリンクURLをクローリングするための辞書(hostName_remaining)に登録
    hostName_remaining[host] = {URL_list: [(deque)], update_time: int(time.time())}

    args:
        url_tuple: 追加したいURL(Todo: タプルの中身)
    """

    # ホスト名を抽出
    host_name = urlparse(url_tuple[0]).netloc
    if host_name not in hostName_remaining:
        # ホスト名がクローリングリストに存在しなければ追加
        hostName_remaining[host_name] = dict()
        hostName_remaining[host_name]['URL_list'] = deque()    # URLの待機リスト
        hostName_remaining[host_name]['update_time'] = 0       # 待機リストからURLが取り出された時間
    hostName_remaining[host_name]['URL_list'].append(url_tuple)


def del_child(now: int):
    """
    hostName_processの整理
    - 死んでいるプロセスの情報を辞書から削除、queueの削除
    - 子プロセスが終了しない、子のメインループも回ってなく、どこかで止まっている場合、親から強制終了
    - 基準は、待機キューの更新が300秒以上なかったら

    args:
        now: ToDo
    """

    del_process_list: List[str] = list()
    for host_name, process_dc in hostName_process.items():
        if process_dc.is_alive():
            # プロセスが生きている
            logger.debug('alive process: %d, %s', process_dc.pid, process_dc.name)
            # 通信路が空だった最後の時間をリセット
            if 'latest_time' in hostName_queue[host_name]:
                del hostName_queue[host_name]['latest_time']
            # 300秒間子プロセスから通信がなかった場合は強制終了する
            if host_name in hostName_remaining:
                update_time: int = hostName_remaining[host_name]["update_time"]
                if update_time and ((now - update_time) > 300):
                    # update_timeに時間が入っていて、かつ300秒経っていた場合終了しnotice.txtに記録
                    process_dc.terminate()
                    hostName_remaining[host_name]["update_time"] = 0
                    logger.info("terminate %s, Over 300 seconds.", str(process_dc))
                    w_file('notice.txt', str(process_dc) + ' is deleted.\n', mode="a")
        else:
            # プロセスが死んでいる
            if host_name in hostName_remaining:
                # ホスト最終更新時間をリセット
                hostName_remaining[host_name]["update_time"] = 0
            # 死んでいて、かつ通信路が空ならば、そのときの時間を保存(メモリ解放のため)
            if 'latest_time' not in hostName_queue[host_name]:
                if hostName_queue[host_name]['child_send'].empty() and hostName_queue[host_name]['parent_send'].empty():
                    hostName_queue[host_name]['latest_time'] = now

        # 死んでいたプロセスのインスタンスを削除(メモリ解放のため)
        # 基準は死んでいるプロセスで、かつ通信路が60秒以上空の場合
        if 'latest_time' in hostName_queue[host_name]:
            if now - hostName_queue[host_name]['latest_time'] > 60:
                del_process_list.append(host_name)


def crawler_host(queue_log: Queue[Any], org_arg: Dict[str, Union[str, int]] = {}):
    """
    こいつはなに、強そう
    Crawring開始処理, プロセスとして作成される
    データを入れる/RADの作成

    Args:
        org_arg
        queue_log: プロセスが作成された際にログを一つにまとめるためのキュー
    """

    global nth, org_path
    # spawnで子プロセスを生成しているかチェック(windowsではデフォ、unixではforkがデフォ)
    worker_configurer(queue_log, logger)
    logger.debug('crawler_host process started')

    if org_arg is None:
        os._exit(255) # type: ignore

    nth = org_arg['result_no'] # str型  result_historyの中のresultの数+1(何回目のクローリングか)
    org_path = cast(str, org_arg['org_path'])   # 組織ごとのディレクトリパス。設定ファイルや結果を保存するところ "/home/.../organization/組織名"

    global hostName_achievement, hostName_process, hostName_queue, hostName_remaining, fewest_host
    global url_list, assignment_url_set
    global remaining, send_num, recv_num, all_achievement
    start = int(time())

    # 設定データを読み込み
    setting_dict = get_setting_dict(path=org_path + '/ROD/LIST')

    if None in setting_dict.values():
        # 設定が読み込めなかった場合にエラーを出して終了
        logger.error("check the SETTING.txt in %s/ROD/LIST", org_path)
        sleep(1)
        os._exit(255) # type: ignore

    assign_or_achievement = setting_dict['assignOrAchievement']
    max_process = cast(int, setting_dict['MAX_process'])
    max_page = cast(int, setting_dict['MAX_page'])
    max_time = setting_dict['MAX_time']
    save_time = cast(int, setting_dict['SAVE_time'])
    run_count = cast(int, setting_dict['run_count'])
    screenshots = cast(bool, setting_dict['screenshots'])

    # 一回目の実行の場合
    if run_count == 0:
        if os.path.exists(org_path + '/RAD'):
            # すでに/RADが存在しているならエラーを返す
            logger.error("""
    RAD directory exists.
    If this running is at first time, please delete this one.
    Else, you should check the run_count in SETTING.txt.""")
            sleep(1)
            os._exit(255) # type: ignore

        os.mkdir(org_path + '/RAD')
        make_dir(screenshots=screenshots)
        copytree(org_path + '/ROD/url_hash_json', org_path + '/RAD/url_hash_json')
        copytree(org_path + '/ROD/tag_data', org_path + '/RAD/tag_data')
        if os.path.exists(org_path + '/ROD/url_db'):
            copyfile(org_path + '/ROD/url_db', org_path + '/RAD/url_db')
        with open(org_path + '/RAD/READ.txt', 'w') as f:
            f.writelines(["This directory's files can be read and written.\n",
                "On the other hand, ROD directory's files are not written, Read Only Data.\n\n",
                "------------------------------------\n",
                "When crawling is finished, you should overwrite the ROD/...\n",
                "tag_data/, url_hash_json/\n",
                "... by this directory's ones for next crawling by yourself.\n",
                "Then, you move df_dict in this directory to ROD/df_dicts/ to calculate idf_dict.\n",
                "After you done these, you may delete this(RAD) directory.\n",
                "To calculate idf_dict, you must run 'tf_idf.py'.\n",
                "------------------------------------\n",
                "Above mentioned comment can be ignored.\n",
                "Because it is automatically carried out."])

    # 必要なリストを読み込む
    import_file(path=org_path + '/ROD/LIST')

    # org_path + /result に移動
    try:
        os.chdir(org_path + '/result')
    except FileNotFoundError:
        logger.error('You should check the run_count in setting file.')

    # メモリ使用量監視スレッドの立ち上げ
    t: MemoryObserverThread = MemoryObserverThread(queue_log)
    t.setDaemon(True) # daemonにすることで、メインスレッドはこのスレッドが生きていても死ぬことができる
    t.start()
    if not t:
        logger.error("Fail to open memory observer thread")

    # メインループを回すループ(save_timeが設定されていなければ、途中保存しないため一周しかしない。一周で全て周り切る)
    while True:
        save = False
        remaining = 0
        send_num = 0                     # 途中経過表示 5秒ごとに子プロセスに送ったURL数
        recv_num = 0                     # 途中経過表示 5秒ごとに子プロセスから受け取ったURL数
        hostName_process = dict()        # ホスト名 : 子プロセス
        hostName_remaining = dict()      # ホスト名 : 待機URLのキュー
        hostName_queue = dict()          # ホスト名 : 通信用キュー
        hostName_achievement = dict()    # ホスト名 : 達成数
        fewest_host = None
        url_list = deque()               # (URL, リンク元)のタプルのリスト。URLをhostName_remainingに割り振る前に保存しておくところ
        assignment_url_set = set()       # 割り当て済みのURLの集合
        all_achievement = 0
        current_start_time = time()
        pre_time = int(current_start_time)    # 10秒毎に進捗を表示するために時間を記録

        # init()から返ってきたとき、実行ディレクトリは result からその中の result/result_* に移動している
        if not init(queue_log, process_run_count=run_count, setting_dict=setting_dict):
            os._exit(255) # type: ignore

        # メインループ
        while True:
            current_achievement = get_achievement_amount()
            remaining = len(url_list) + sum([len(dic['URL_list']) for dic in hostName_remaining.values()])
            receive_and_send()
            now = int(time())

            # 10秒ごとに途中経過表示
            if now - pre_time > 10:
                del_child(now)
                print_progress(now - int(current_start_time), current_achievement)
                pre_time = now

            # 途中保存関連オプション
            if max_time:
                # max_timeオプションが指定されている場合
                if now - start >= int(max_time):
                    # 指定時間経過したら
                    logger.info('Spend time reached to MAX_time')
                    forced_termination()
                    break

            ####################
            ### Todo
            ### 開発用Option
            if assign_or_achievement:
                # assign_or_achievementオプションが指定されていた場合
                if len(assignment_url_set) >= max_page:
                    # 指定数URLをアサインしたら
                    logger.info('Number of assignment reached MAX')
                    while not (get_alive_child_num() == 0):
                        # 子プロセスがすべて終了するまで待つ
                        sleep(3)
                        for temp in hostName_process.values():
                            if temp.is_alive():
                                logger.debug("alived process [%s]", str(temp))
                    break
            #####################
            ### Todo
            ### ここのelse不要では?
            else:
                # 指定数URLを達成したら
                if (all_achievement + current_achievement) >= max_page:
                    logger.info("Num of achievement reached MAX")
                    forced_termination()
                    break
            ######################

            # 指定した時間経過すると実行結果を全て保存する
            # プログラム本体は終わらず、メインループを再スタートする
            if save_time:
                if now - int(current_start_time) >= save_time:
                    forced_termination()
                    save = True
                    break

            # 終了条件
            if end():
                # url_dbから過去発見したURLを取ってきて、クローリングしていないのがあればurl_listに追加する
                # TODO: うまく動いていない可能性あり
                try:
                    k = url_db.firstkey()
                    url_db_set = set()
                    while k is not None:
                        # url_dbにデータがある間ループする
                        content: str = url_db[k].decode("utf-8")
                        if "True" in content:
                            # url_dbからクローリングすべきurlたちをurl_db_setに追加する
                            url: str = k.decode("utf-8")
                            url_db_set.add(url)
                        k = url_db.nextkey(k)
                    # すでに探索したurlとurl_dbから取った探索すべきurlの差集合をとる
                    not_achieved = url_db_set.difference(assignment_url_set)
                    if not_achieved:
                        # 探索していないurlをurl_listに追加する
                        for url in not_achieved:
                            url_list.append((url, "url_db"))
                    else:
                        # すべてのURLが探索済みであれば回ったurlを更新して終了
                        all_achievement += current_achievement
                        w_json(name='assignment_url_set', data=list(assignment_url_set))
                        break
                except Exception:
                    all_achievement += current_achievement
                    w_json(name='assignment_url_set', data=list(assignment_url_set))
                    break

            # url_list(まだクローリングしていないURLのリスト)からURLのタプルを取り出してホスト名で分類
            while url_list:
                url_tuple = url_list.popleft()
                # ホスト名ごとに分け、子プロセスへの送信待ちリストに追加
                allocate_to_host_remaining(url_tuple=url_tuple)

            # プロセス数が上限に達していなければ、プロセスを生成する
            # falsification.cysecは最優先で周る機能
            # host = 'falsification.cysec.cs.ritsumei.ac.jp'
            # if host in hostName_remaining:
            #     if hostName_remaining[host]['URL_list']:
            #         if host in hostName_process:
            #             if not hostName_process[host].is_alive():
            #                 make_process(host, setting_dict)
            #         else:
            #             make_process(host, setting_dict)

            # 生成可能なプロセス数を計算しプロセスを作成する
            num_of_runnable_process: int = max_process - get_alive_child_num()
            if num_of_runnable_process > 0:
                # プロセス数にゆとりがあるならば
                # hostName_remainingを待機URL数が多い順にソートする
                tmp_list = sorted(hostName_remaining.items(), reverse=True, key=lambda kv: len(kv[1]['URL_list']))
                # 待機(URL_list)が0のサーバーを削除
                tmp_list = [tmp for tmp in tmp_list if tmp[1]['URL_list']]
                if tmp_list:
                    # 一番待機URLが少ないホスト名のクローロングプロセスを1つ作る
                    fewest_host_now = tmp_list[-1][0]
                    make_fewest_host_proc_flag = True
                    if fewest_host is not None:
                        # もしすでに最も待機の少ないホストのクローリングプロセスを作っていたなら
                        if fewest_host in hostName_process:
                            if hostName_process[fewest_host].is_alive():
                                ##### Todo: first
                                # ここ死んでるならばじゃね????
                                # クローリングプロセスがまだ生きているならば
                                make_fewest_host_proc_flag = False
                                ########
                    if make_fewest_host_proc_flag:
                        # 現在もっとも待機数の少ないホストをクローリングしていないならプロセス作成
                        make_process(fewest_host_now, queue_log, setting_dict)
                        num_of_runnable_process -= 1
                        fewest_host = fewest_host_now

                    # 待機URLが多い順にクローリングプロセスを作る
                    for host_url_list_tuple in tmp_list:
                        # tmp_listの各要素: (ホスト名, remaining辞書)のタプル
                        if num_of_runnable_process <= 0:
                            break
                        if host_url_list_tuple[0] in hostName_process:
                            if hostName_process[host_url_list_tuple[0]].is_alive():
                                continue   # プロセスが活動中なら、次に多いホストをtmp_listから探す
                        make_process(host_url_list_tuple[0], queue_log, setting_dict)
                        num_of_runnable_process -= 1

        # すべてのURLを探索し終わったや規定数に探索が達したならメインループを抜け、結果表示＆保存
        remaining = len(url_list) + sum([len(dic['URL_list']) for dic in hostName_remaining.values()])
        current_achievement = get_achievement_amount()
        run_time = int(time()) - int(current_start_time)
        logger.info(f"""
    --------------result-----------------
    assignment_url_set  = {str(len(assignment_url_set))}
    current achievement = {str(current_achievement)}
    all achievement     = {str(all_achievement)}
    Num of child-proc   = {str(len(hostName_achievement))}
    run time            = {str(run_time)}
    remaining           = {str(remaining)}
    -------------------------------------""")
        w_file('result.txt', 'assignment_url_set = ' + str(len(assignment_url_set)) + '\n' +
               'current achievement = ' + str(current_achievement) + '\n' +
               'all achievement = ' + str(all_achievement) + '\n' +
               'number of child-process = ' + str(len(hostName_achievement)) + '\n' +
               'run time = ' + str(run_time) + '\n' +
               'remaining = ' + str(remaining) + '\n' +
               'date = ' + datetime.datetime.now().strftime('%Y/%m/%d, %H:%M:%S') + '\n', mode="a")

        logger.info("Result Saving....")
        copytree(org_path + '/RAD', 'TEMP')
        logger.info("Result Saving.... FIN!")

        # if setting_dict['machine_learning']:
        #     print('main : wait for machine learning process')
        #     machine_learning_q['recv'].put('end')       # 機械学習プロセスに終わりを知らせる
        #     if not machine_learning_q['process'].join(timeout=60):  # 機械学習プロセスが終わるのを待つ
        #         print("main : Terminate machine-learning proc.")
        #         machine_learning_q['process'].terminate()
        # if setting_dict['screenshots_svc']:
        #     print('main : wait for screenshots learning process')
        #     screenshots_svc_q['recv'].put('end')       # 機械学習プロセスに終わりを知らせる
        #     if not screenshots_svc_q['process'].join(timeout=60):  # 機械学習プロセスが終わるのを待つ
        #         print("main : Terminate screenshots-svc proc.")
        #         screenshots_svc_q['process'].terminate()

        if setting_dict['clamd_scan']:
            # clamdプロセスを終了させる
            logger.info("Wait for clamd process finish...")
            clamd_q['recv'].put('end')
            if not clamd_q['process'].join(timeout=60):
                # 終わるまで待機
                logger.info("Terminate Clamd proc")
                clamd_q['process'].terminate()

        # summarize alertプロセス終了処理
        logger.info("Wait for summarize alert process")
        summarize_alert_q['recv'].put('end')
        if not summarize_alert_q['process'].join(timeout=60):
            # 終わるまで待機
            logger.info("Terminate summarize-alert proc.")
            summarize_alert_q['process'].terminate()

        url_db.close()
        # メインループをもう一度回すかどうか
        if save and remaining:  # saveフラグが立っていても, remaining=0の場合はクローリングを終える
            logger.info('Restart...')
            run_count += 1
            os.chdir('..')
        else:
            os.chdir('..')
            break

    logger.info('Finish!')
