﻿from multiprocessing import Process, Queue, cpu_count, get_context
from urllib.parse import urlparse
from collections import deque
from time import time, sleep
import os
from datetime import datetime
from clamd import clamd_main
from shutil import copytree, copyfile
import dbm
import pickle
import json

# from machine_learning_screenshots import screenshots_learning_main
# from machine_learning_tag import machine_learning_main
from crawler3 import crawler_main
from file_rw import r_file, w_json, r_json, w_file
from summarize_alert import summarize_alert_main
from sys_command import kill_chrome
from resources_observer import MemoryObserverThread


filtering_dict = dict()     # 接続すべきURLかどうか判断するのに必要なリストをまとめた辞書
clamd_q = dict()
machine_learning_q = dict()
screenshots_svc_q = dict()
summarize_alert_q = dict()

# これらホスト名辞書はまとめてもいいが、まとめるとどこで何を使ってるか分かりにくくなる
hostName_remaining = dict()    # ホスト名 : {"URL_list": 待機URLのリスト, "update_time": リストからURLをpopした時の時間}
hostName_achievement = dict()  # ホスト名 : 達成数
# 以下の三つはkeyの作成、削除タイミングが同じ
hostName_process = dict()      # ホスト名 : 子プロセス
hostName_queue = dict()        # ホスト名 : 通信キュー
hostName_args = dict()         # ホスト名 : 子プロセスの引数
fewest_host = None             # 待機URL数が一番少ないホスト名

url_db = None                  # key-valueデータベース. URL : (True or False or Black or Unknown or Special) + , +  nth
nth = None                     # 何回目のクローリングか
org_path = ""                  # 組織ごとのディレクトリの絶対パス  /home/ユーザ名/.../organization/組織名

url_list = deque()             # (URL, リンク元)のタプルのリスト(子プロセスに送信用)
assignment_url_set = set()     # 割り当て済みのURLの集合
remaining = 0  # 途中保存で終わったときの残りURL数
send_num = 0  # 途中経過で表示する5秒ごとの子プロセスに送ったURL数
recv_num = 0  # 途中経過で表示する5秒ごとの子プロセスから受け取ったURL数
all_achievement = 0


# 設定ファイルの読み込み
def get_setting_dict(path):
    setting = dict()
    bool_variable_list = ['assignOrAchievement', 'screenshots', 'clamd_scan', 'machine_learning', 'headless_browser',
                          'mecab', 'screenshots_svc']
    setting_file = r_file(path + '/SETTING.txt')
    setting_line = setting_file.split('\n')
    for line in setting_line:
        if line and not line.startswith('#'):
            variable = line[0:line.find('=')]
            right_side = line[line.find('=')+1:]
            if variable == 'MAX_page':
                try:
                    value = int(right_side)    # 文字(小数点も)をはじく.でも空白ははじかないみたい
                except ValueError:
                    print("main : couldn't import setting file. because of MAX_page.")
                    setting['MAX_page'] = None
                else:
                    setting['MAX_page'] = value
            elif variable == 'MAX_time':
                right_side_split = right_side.split('*')
                value = 1
                try:
                    for i in right_side_split:
                        value *= int(i)
                except ValueError:
                    print("main : couldn't import setting file. because of MAX_time.")
                    setting['MAX_time'] = None
                else:
                    setting['MAX_time'] = value
            elif variable == 'SAVE_time':
                right_side_split = right_side.split('*')
                value = 1
                try:
                    for i in right_side_split:
                        value *= int(i)
                except ValueError:
                    print("main : couldn't import setting file. because of SAVE_time.")
                    setting['SAVE_time'] = None
                else:
                    setting['SAVE_time'] = value
            elif variable == 'run_count':
                try:
                    value = int(right_side)
                except ValueError:
                    print("main : couldn't import setting file. because of run_count.")
                    setting['run_count'] = None
                else:
                    setting['run_count'] = value
            elif variable == 'MAX_process':
                try:
                    value = int(right_side)
                except ValueError:
                    print("main : couldn't import setting file. because of MAX_process.")
                    setting['MAX_process'] = None
                else:
                    if value == 0:
                        setting['MAX_process'] = cpu_count()
                    elif value < 0:
                        setting['MAX_process'] = cpu_count() + value if cpu_count() + value > 0 else 1
                    else:
                        setting['MAX_process'] = value
            elif variable in bool_variable_list:   # True or Falseの2値しか取らない設定はまとめている
                if right_side == 'True':
                    setting[variable] = True
                elif right_side == 'False':
                    setting[variable] = False
                else:
                    print("main : couldn't import setting file. because of " + variable + '.')
                    setting[variable] = None
            else:
                print("main : couldn't import setting file. because of exist extra setting.")
                print("main : what's " + variable)
                setting['extra'] = None
    return setting


# 必要なリストをインポート
def import_file(path):             # 実行でディレクトリは「crawler」
    filter_list = ["DOMAIN", "WHITE", "IPAddress", "REDIRECT", "BLACK"]
    for filter_ in filter_list:
        if os.path.exists("{}/{}.json".format(path, filter_)):
            with open("{}/{}.json".format(path, filter_), "r") as f:
                filtering_dict[filter_] = json.load(f)
        else:
            filtering_dict[filter_] = dict()


# 必要なディレクトリを作成
def make_dir(screenshots):          # 実行ディレクトリは「crawler」
    # RODディレクトリ : 過去のデータなど。クローリングで参照するデータ。
    # RADディレクトリ : 今回集めるデータを保存する場所。このデータは次回以降のクローリングで使用する。クローリング中に更新していく。
    # resultディレクトリ : 今回のクローリング結果を保存する場所。
    dir_list = ["/ROD/url_hash_json", "/ROD/tag_data", "/ROD/df_dicts", "/RAD/df_dict", "/RAD/temp", "/result"]
    # 必要なディレクトリがなければ作る,
    for dir_name in dir_list:
        if not os.path.exists(org_path + dir_name):
            os.mkdir(org_path + dir_name)
    if screenshots:
        if not os.path.exists(org_path + '/RAD/screenshots'):
            os.mkdir(org_path + '/RAD/screenshots')


# いろいろと最初の処理
def init(first_time, setting_dict):    # 実行ディレクトリは「result」、最後の方に「result_*」に移動
    global url_db
    url_db = dbm.open(org_path + '/RAD/url_db', 'c')  # url_dbの作成

    machine_learning_ = setting_dict['machine_learning']
    clamd_scan = setting_dict['clamd_scan']
    screenshots_svc = setting_dict['screenshots_svc']

    global all_achievement
    # 検索済みURL、検索待ちURLなど、途中保存データを読み込む。
    if first_time == 0:  # 一回目の実行の場合は、START_LISTだけ読み込む。
        data_temp = r_file(org_path + '/ROD/LIST/START_LIST.txt')
        data_temp = data_temp.split('\n')
        url_list.extend([(ini, "START") for ini in data_temp if ini])
    else:
        if not os.path.exists('result_' + str(first_time)):
            print('init : result_' + str(first_time) + ' that is the result of previous crawling is not found.')
            return False
        # 総達成数
        data_temp = r_json('result_' + str(first_time) + '/all_achievement')
        all_achievement = data_temp
        # 子プロセスに割り当てたURLの集合
        data_temp = r_json('result_' + str(first_time) + '/assignment_url_set')
        assignment_url_set.update(set(data_temp))
        # ホスト名を見て分類する前のリスト
        data_temp = r_json('result_' + str(first_time) + '/url_list')
        url_list.extend([tuple(i) for i in data_temp])
        # 各ホストごとに分類されたURLのリストの辞書
        with open('result_' + str(first_time) + '/host_remaining.pickle', 'rb') as f:
            data_temp = pickle.load(f)
        hostName_remaining.update(data_temp)
        for host_name in hostName_remaining.keys():
            hostName_remaining[host_name]["update_time"] = 0

    # 作業ディレクトリを作って移動
    try:
        os.mkdir('result_' + str(first_time + 1))
        os.chdir('result_' + str(first_time + 1))
    except FileExistsError:
        print('init : result_' + str(first_time + 1) + ' directory has already made.')
        return False
    # summarize_alertのプロセスを起動
    recvq = Queue()
    sendq = Queue()
    summarize_alert_q['recv'] = recvq  # 子プロセスが受け取る用のキュー
    summarize_alert_q['send'] = sendq  # 子プロセスから送信する用のキュー
    p = Process(target=summarize_alert_main, args=(recvq, sendq, nth, org_path))
    p.daemon = True
    p.start()
    summarize_alert_q['process'] = p

    # clamdを使うためのプロセスを起動(その子プロセスでclamdを起動)
    if clamd_scan:
        recvq = Queue()
        sendq = Queue()
        clamd_q['recv'] = recvq   # clamdプロセスが受け取る用のキュー
        clamd_q['send'] = sendq   # clamdプロセスから送信する用のキュー
        p = Process(target=clamd_main, args=(recvq, sendq, org_path))
        p.daemon = True
        p.start()
        clamd_q['process'] = p
        if sendq.get(block=True):
            print('main : connect to clamd')   # clamdに接続できたようなら次へ
        else:
            print("main : couldn't connect to clamd")  # できなかったようならFalseを返す
            return False
    if machine_learning_:
        """
        # 機械学習を使うためのプロセスを起動
        recvq = Queue()
        sendq = Queue()
        machine_learning_q['recv'] = recvq
        machine_learning_q['send'] = sendq
        p = Process(target=machine_learning_main, args=(recvq, sendq, '../../ROD/tag_data'))
        p.start()
        machine_learning_q['process'] = p
        print('main : wait for machine learning...')
        print(sendq.get(block=True))   # 学習が終わるのを待つ(数分？)
        """
        print("main : cant use machine-learning.")
        return False
    if screenshots_svc:
        """
        # 機械学習を使うためのプロセスを起動
        recvq = Queue()
        sendq = Queue()
        screenshots_svc_q['recv'] = recvq
        screenshots_svc_q['send'] = sendq
        p = Process(target=screenshots_learning_main, args=(recvq, sendq, '../../ROD/screenshots'))
        p.start()
        screenshots_svc_q['process'] = p
        print('main : wait for screenshots learning...')
        print(sendq.get(block=True))   # 学習が終わるのを待つ(数分？)
        """
        print("main : cant use screenshots-svc.")
        return False
    return True


# 各子プロセスの達成数を足し合わせて返す
# 達成数 = ページ数(リンク集が返ってきた数) + ファイル数(ファイルの達成通知の数)
def get_achievement_amount():
    achievement = 0
    for achievement_num in hostName_achievement.values():
        achievement += achievement_num
    return achievement


# 10秒ごとに途中経過表示、メインループが動いてることの確認のため、スレッド化していない
def print_progress(run_time_pp, current_achievement):
    global send_num, recv_num
    alive_count = get_alive_child_num()
    print('main : ---------progress--------', flush=True)

    count = 0
    for host, remaining_dict in hostName_remaining.items():
        remaining_num = len(remaining_dict['URL_list'])

        if remaining_num == 0:
            count += 1    # URL待機リストが空のホスト数をカウント
        else:
            pass
            # if host in hostName_process:
            #     print('main : ' + host + "'s remaining is " + str(remaining_num) +
            #           '\t active = ' + str(hostName_process[host].is_alive()))
            # else:
            #     print('main : ' + host + "'s remaining is " + str(remaining_num) + "\t active = isn't made")
    print('main : remaining=0 is ' + str(count), flush=True)
    print('main : run time = ' + str(run_time_pp) + 's.', flush=True)
    print('main : recv-URL : send-URL = ' + str(recv_num) + ' : ' + str(send_num), flush=True)
    print("main : achievement/assignment = {} / {}".format(current_achievement, len(assignment_url_set)), flush=True)
    print('main : all achievement = ' + str(all_achievement + current_achievement), flush=True)
    print('main : alive child process = ' + str(alive_count), flush=True)
    print('main : remaining = ' + str(remaining), flush=True)
    print('main : -------------------------', flush=True)
    send_num = 0
    recv_num = 0


# 強制終了させるために途中経過を保存する
def forced_termination():
    global all_achievement
    print('main : forced_termination', flush=True)

    # 子プロセスがなくなるまで回り続ける
    while get_alive_child_num() > 0:
        receive_and_send(not_send=True)   # 子プロセスからのデータを抜き取る
        for host_name, host_name_remaining in hostName_remaining.items():
            length = len(host_name_remaining['URL_list'])
            if length:
                print('main : ' + host_name + ' : remaining --> ' + str(length), flush=True)
        print('main : wait for finishing alive process ' + str(get_alive_child_num()), flush=True)
        del_child(int(time()))
        sleep(3)

    # 続きをするために途中経過を保存する
    all_achievement += get_achievement_amount()
    w_json(name='url_list', data=list(url_list))
    w_json(name='assignment_url_set', data=list(assignment_url_set))
    w_json(name='all_achievement', data=all_achievement)
    with open('host_remaining.pickle', 'wb') as f:
        pickle.dump(hostName_remaining, f)


# 全ての待機キューにURLがなく、全ての子プロセスが終了していたらTrue
def end():
    if url_list:                # 子プロセスに送るためのURLのリストが空で
        return False
    if get_alive_child_num():   # 生きている子プロセスがいなくて
        return False
    for host, remaining_temp in hostName_remaining.items():  # キューに要素があるかどうか
        if len(remaining_temp['URL_list']):
            return False
    return True


# クローリングプロセスを生成する、既に一度作ったことがある場合は、プロセスだけ作る
def make_process(host_name, setting_dict):
    if host_name not in hostName_process:   # まだ作られていない場合、プロセス作成
        # 子プロセスと通信するキューを作成
        child_sendq = Queue()
        parent_sendq = Queue()

        # 子プロセスに渡す引数を辞書にまとめる
        args_dic = dict()
        args_dic['host_name'] = host_name
        args_dic['parent_sendq'] = parent_sendq
        args_dic['child_sendq'] = child_sendq
        args_dic['alert_process_q'] = summarize_alert_q['recv']
        if setting_dict['clamd_scan']:
            args_dic['clamd_q'] = clamd_q['recv']
        else:
            args_dic['clamd_q'] = False
        if setting_dict['machine_learning']:
            args_dic['machine_learning_q'] = machine_learning_q['recv']
        else:
            args_dic['machine_learning_q'] = False
        if setting_dict['screenshots_svc']:
            args_dic['screenshots_svc_q'] = screenshots_svc_q['recv']
        else:
            args_dic['screenshots_svc_q'] = False
        args_dic['nth'] = nth
        args_dic['headless_browser'] = setting_dict['headless_browser']
        args_dic['mecab'] = setting_dict['mecab']
        args_dic['screenshots'] = setting_dict['screenshots']
        args_dic['org_path'] = org_path
        args_dic["filtering_dict"] = filtering_dict
        hostName_args[host_name] = args_dic    # クローラプロセスの引数は、サーバ毎に毎回同じなので保存しておく

        # プロセス作成
        p = Process(target=crawler_main, name=host_name, args=(hostName_args[host_name],))
        p.daemon = True   # 親が死ぬと子も死ぬ
        p.start()    # スタート

        # クローリングプロセスに関わる設定データを保存
        hostName_process[host_name] = p
        hostName_queue[host_name] = {'child_send': child_sendq, 'parent_send': parent_sendq}
        if host_name not in hostName_achievement:
            hostName_achievement[host_name] = 0
        print('main : ' + host_name + " 's process start. " + 'pid = ' + str(p.pid))
    else:
        del hostName_process[host_name]
        print('main : ' + host_name + ' is not alive.')
        # プロセス作成
        p = Process(target=crawler_main, name=host_name, args=(hostName_args[host_name],))
        p.daemon = True     # 親が死ぬと子も死ぬ
        p.start()   # スタート
        hostName_process[host_name] = p   # プロセスを指す辞書だけ更新する
        print('main : ' + host_name + " 's process start. " + 'pid =' + str(p.pid))


# クローリング子プロセスの中で生きている数を返す
def get_alive_child_num():
    count = 0
    for host_temp in hostName_process.values():
        if host_temp.is_alive():
            count += 1
    return count


# 子プロセスからの情報を受信する、plzを受け取るとURLを送信する
# 受信したリストの中のURLはクローリングするURLならばurl_listに追加する。
# not_send=Trueのとき、子プロセスにはURLを送信しない。子プロセスからのデータを受け取りたいだけの時に使う。
def receive_and_send(not_send=False):
    # 受信する型は、辞書、タプル、文字列の3種類
    # {'type': '文字列', 'url_set': [(url, 検査結果), (url, 検査結果),...], "page_url": URLが貼ってあったページURL, オプション}の辞書
    # (url, 'redirect')のタプル(リダイレクトが起こったが、ホスト名が変わらなかったためそのまま処理された場合)
    # "receive"の文字(子プロセスがURLのタプルを受け取るたびに送信する)
    # "plz"の文字(子プロセスがURLのタプルを要求)
    global recv_num, send_num
    for host_name, queue in hostName_queue.items():
        try:
            received_data = queue['child_send'].get(block=False)
        except Exception:   # queueにデータがなければエラーが出る
            continue
        if type(received_data) is str:       # 子プロセスが情報を受け取ったことの確認
            if received_data == 'plz':     # URLの送信要求の場合
                hostName_remaining[host_name]['update_time'] = int(time())
                if not_send is True:
                    queue['parent_send'].put('nothing')
                else:
                    if hostName_remaining[host_name]['URL_list']:
                        # クローリングするurlを送信
                        while True:
                            url_tuple = hostName_remaining[host_name]['URL_list'].popleft()
                            if url_tuple[0] not in assignment_url_set:  # まだ送信していないURLならば
                                assignment_url_set.add(url_tuple[0])
                                queue['parent_send'].put(url_tuple)
                                send_num += 1
                                break  # 一つでもURLを送信したらbreak
                            if not hostName_remaining[host_name]['URL_list']:  # 待機リストが空になるとbreak
                                queue['parent_send'].put('nothing')  # もうURLが残ってないことを教える
                                break
                    else:
                        queue['parent_send'].put('nothing')  # もうURLが残ってないことを教える

        elif type(received_data) is tuple:      # リダイレクトしたが、ホスト名が変わらなかったため子プロセスで処理を続行
            assignment_url_set.add(received_data[0])  # リダイレクト後のURLを割り当てURL集合に追加
            url_db[received_data[0]] = 'True,' + str(nth)
        elif type(received_data) is dict:
            url_tuple_set = set()
            page_url = "NOON"
            if "url_set" in received_data:
                url_tuple_set = received_data["url_set"]
            if "page_url" in received_data:
                page_url = received_data["page_url"]

            if received_data['type'] == 'links':
                hostName_achievement[host_name] += 1   # ページクローリング結果なので、検索済み数更新
            elif received_data['type'] == 'file_done':
                hostName_achievement[host_name] += 1   # ファイルクローリング結果なので、検索済み数更新して次へ
                continue
            elif received_data['type'] == 'new_window_url':      # 新しい窓(orタブ)に出たURL(今のところ見つかってない)
                for url_tuple in url_tuple_set:
                    data_temp = dict()
                    data_temp['url'] = url_tuple[0]
                    data_temp['src'] = page_url
                    data_temp['file_name'] = 'new_window_url.csv'
                    data_temp['content'] = url_tuple[0] + ',' + page_url
                    data_temp['label'] = 'NEW_WINDOW_URL,URL'
                    summarize_alert_q['recv'].put(data_temp)
            elif received_data['type'] == 'redirect':  # リダイレクトの場合、URLがホワイトリストにかからなければアラート
                url, res = list(url_tuple_set)[0]   # リダイレクトの場合、集合の要素数は１個だけ
                if (res is False) or (res == "Unknown"):  # 外部URLだった場合
                    redirect_host = urlparse(url).netloc
                    redirect_path = urlparse(url).path
                    w_alert_flag = True
                    # ホスト名+パスの途中までを見てホワイトリストに引っかからなければアラート
                    for white_host, white_path_list in filtering_dict["REDIRECT"]["allow"].items():
                        if redirect_host.endswith(white_host) and \
                                [wh_pa for wh_pa in white_path_list if redirect_path.startswith(wh_pa)]:
                            w_alert_flag = False
                            break
                    if w_alert_flag:
                        data_temp = dict()
                        data_temp['url'] = url
                        data_temp['src'] = page_url
                        data_temp['file_name'] = 'after_redirect_check.csv'
                        data_temp['content'] = received_data["ini_url"] + ',' + page_url + ',' + url
                        data_temp['label'] = 'URL,SOURCE,REDIRECT_URL'
                        summarize_alert_q['recv'].put(data_temp)
                w_file('after_redirect.csv', received_data["ini_url"] + ',' + received_data["page_url"] + ',' +
                       url + "," + str(res) + '\n', mode="a")

            # urlリストに追加。既に割り当て済みの場合は追加しない。
            if url_tuple_set:
                recv_num += len(url_tuple_set)
                # 接続診断結果がTrueのURLをurl_listに追加
                for url_tuple in url_tuple_set:
                    if url_tuple[1] is True:
                        url_list.append((url_tuple[0], page_url))    # 分類待ちリストに入れる
                    # url_dbの更新
                    url_db[url_tuple[0]] = str(url_tuple[1]) + ',' + str(nth)


# url_tupleのリンクURLをクローリングするための辞書に登録する
# hostName_remaining[host] = {URL_list: [], update_time: int(time.time())}
def allocate_to_host_remaining(url_tuple):
    host_name = urlparse(url_tuple[0]).netloc
    if host_name not in hostName_remaining:
        hostName_remaining[host_name] = dict()
        hostName_remaining[host_name]['URL_list'] = deque()    # URLの待機リスト
        hostName_remaining[host_name]['update_time'] = 0       # 待機リストからURLが取り出されたら、その時の時間が入る
    hostName_remaining[host_name]['URL_list'].append(url_tuple)


# hostName_processの整理(死んでいるプロセスのインスタンスを削除、queueの削除)
# 子プロセスが終了しない、子のメインループも回ってなく、どこかで止まっている場合、親から強制終了させる
# 基準は、待機キューの更新が300秒以上なかったら
def del_child(now):
    del_process_list = list()
    for host_name, process_dc in hostName_process.items():
        if process_dc.is_alive():
            print('main : alive process : ' + str(process_dc))
            # プロセスが生きているので通信路が空だった最後の時間をリセット
            if 'latest_time' in hostName_queue[host_name]:
                del hostName_queue[host_name]['latest_time']
            # 300秒間子プロセスから通信がなかった場合は強制終了する
            if host_name in hostName_remaining:
                update_time = hostName_remaining[host_name]["update_time"]
                if update_time and ((now - update_time) > 300):   # update_timeに時間が入っていて、かつ300秒経っていた場合
                    process_dc.terminate()  # 300秒間子プロセスから通信がなかったので終了させる
                    hostName_remaining[host_name]["update_time"] = 0
                    print('main : terminate ' + str(process_dc) + '. Over 300 Second.')
                    w_file('notice.txt', str(process_dc) + ' is deleted.\n', mode="a")
        else:  # プロセスが死んでいれば
            if host_name in hostName_remaining:
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
    # # メモリ解放
    # for host_name in del_process_list:
    #     del hostName_args[host_name]
    #     del hostName_process[host_name]
    #     del hostName_queue[host_name]


def crawler_host(org_arg=None):
    global nth, org_path
    # spawnで子プロセスを生成しているかチェック(windowsではデフォ、unixではforkがデフォ)
    print(get_context())

    if org_arg is None:
        os._exit(255)

    nth = org_arg['result_no']      # str型  result_historyの中のresultの数+1(何回目のクローリングか)
    org_path = org_arg['org_path']  # 組織ごとのディレクトリパス。設定ファイルや結果を保存するところ "/home/.../organization/組織名"

    global hostName_achievement, hostName_process, hostName_queue, hostName_remaining, fewest_host
    global url_list, assignment_url_set
    global remaining, send_num, recv_num, all_achievement
    start = int(time())

    # 設定データを読み込み
    setting_dict = get_setting_dict(path=org_path + '/ROD/LIST')
    if None in setting_dict.values():
        print(' main : check the SETTING.txt in ' + org_path + '/ROD/LIST')
        os._exit(255)
    assign_or_achievement = setting_dict['assignOrAchievement']
    max_process = setting_dict['MAX_process']
    max_page = setting_dict['MAX_page']
    max_time = setting_dict['MAX_time']
    save_time = setting_dict['SAVE_time']
    run_count = setting_dict['run_count']
    screenshots = setting_dict['screenshots']

    # 一回目の実行の場合
    if run_count == 0:
        if os.path.exists(org_path + '/RAD'):
            print('RAD directory exists.')
            print('If this running is at first time, please delete this one.')
            print('Else, you should check the run_count in SETTING.txt.')
            os._exit(255)
        os.mkdir(org_path + '/RAD')
        make_dir(screenshots=screenshots)
        copytree(org_path + '/ROD/url_hash_json', org_path + '/RAD/url_hash_json')
        copytree(org_path + '/ROD/tag_data', org_path + '/RAD/tag_data')
        if os.path.exists(org_path + '/ROD/url_db'):
            copyfile(org_path + '/ROD/url_db', org_path + '/RAD/url_db')
        with open(org_path + '/RAD/READ.txt', 'w') as f:
            f.writelines("This directory's files can be read and written.\n")
            f.writelines("On the other hand, ROD directory's files are not written, Read Only Data.\n\n")
            f.writelines('------------------------------------\n')
            f.writelines('When crawling is finished, you should overwrite the ROD/...\n')
            f.writelines('tag_data/, url_hash_json/\n')
            f.writelines("... by this directory's ones for next crawling by yourself.\n")
            f.writelines('Then, you move df_dict in this directory to ROD/df_dicts/ to calculate idf_dict.\n')
            f.writelines('After you done these, you may delete this(RAD) directory.\n')
            f.writelines("To calculate idf_dict, you must run 'tf_idf.py'.\n")
            f.writelines('------------------------------------\n')
            f.writelines('Above mentioned comment can be ignored.\n')
            f.writelines('Because it is automatically carried out.')

    # 必要なリストを読み込む
    import_file(path=org_path + '/ROD/LIST')

    # org_path + /result　に移動
    try:
        os.chdir(org_path + '/result')
    except FileNotFoundError:
        print('You should check the run_count in setting file.')   # もういらないと思うけど

    # メモリ使用量監視スレッド
    t = MemoryObserverThread()
    t.setDaemon(True)  # daemonにすることで、メインスレッドはこのスレッドが生きていても死ぬことができる
    t.start()

    # メインループを回すループ(save_timeが設定されていなければ、途中保存しないため一周しかしない。一周で全て周り切る)
    while True:
        save = False
        remaining = 0
        send_num = 0                     # 途中経過で表示する5秒ごとの子プロセスに送ったURL数
        recv_num = 0                     # 途中経過で表示する5秒ごとの子プロセスから受け取ったURL数
        hostName_process = dict()        # ホスト名 : 子プロセス
        hostName_remaining = dict()      # ホスト名 : 待機URLのキュー
        hostName_queue = dict()          # ホスト名 : キュー
        hostName_achievement = dict()    # ホスト名 : 達成数
        fewest_host = None
        url_list = deque()               # (URL, リンク元)のタプルのリスト(子プロセスに送信用)
        assignment_url_set = set()           # 割り当て済みのURLの集合
        all_achievement = 0
        current_start_time = int(time())
        pre_time = current_start_time

        # init()から返ってきたとき、実行ディレクトリは result からその中の result/result_* に移動している
        if not init(first_time=run_count, setting_dict=setting_dict):
            os._exit(255)

        # メインループ
        while True:
            current_achievement = get_achievement_amount()
            remaining = len(url_list) + sum([len(dic['URL_list']) for dic in hostName_remaining.values()])
            receive_and_send()
            now = int(time())

            # 途中経過表示
            if now - pre_time > 10:
                del_child(now)
                print_progress(now - current_start_time, current_achievement)
                pre_time = now

            # 以下、一気に回すと時間がかかるので、途中保存をして止めたい場合
            if max_time:   # 指定時間経過したら
                if now - start >= max_time:
                    forced_termination()
                    break
            if assign_or_achievement:   # 指定数URLをアサインしたら
                if len(assignment_url_set) >= max_page:
                    print('num of assignment reached MAX')
                    while not (get_alive_child_num() == 0):
                        sleep(3)
                        for temp in hostName_process.values():
                            if temp.is_alive():
                                print(temp)
                    break
            else:    # 指定数URLを達成したら
                if (all_achievement + current_achievement) >= max_page:
                    print('num of achievement reached MAX')
                    forced_termination()
                    break

            # 指定した時間経過すると実行結果を全て保存する。が、プログラム本体は終わらず、メインループを再スタートする
            if save_time:
                if now - current_start_time >= save_time:
                    forced_termination()
                    save = True
                    break

            # 本当の終了条件
            if end():
                all_achievement += current_achievement
                w_json(name='assignment_url_set', data=list(assignment_url_set))
                break

            # url_list(子プロセスに送るURLのタプルのリスト)からURLのタプルを取り出してホスト名で分類する
            while url_list:
                url_tuple = url_list.popleft()
                # ホスト名ごとに分けられている子プロセスに送信待ちリストに追加
                allocate_to_host_remaining(url_tuple=url_tuple)

            # プロセス数が上限に達していなければ、プロセスを生成する
            # falsification.cysecは最優先で周る
            host = 'falsification.cysec.cs.ritsumei.ac.jp'
            if host in hostName_remaining:
                if hostName_remaining[host]['URL_list']:
                    if host in hostName_process:
                        if not hostName_process[host].is_alive():
                            make_process(host, setting_dict)
                    else:
                        make_process(host, setting_dict)

            num_of_runnable_process = max_process - get_alive_child_num()
            if num_of_runnable_process > 0:
                # remainingリストの中で一番待機URL数が多い順プロセスを生成する
                tmp_list = sorted(hostName_remaining.items(), reverse=True, key=lambda kv: len(kv[1]['URL_list']))
                tmp_list = [tmp for tmp in tmp_list if tmp[1]['URL_list']]   # 待機(URL_list)が0以外のサーバーリスト
                if tmp_list:
                    # 一番待機URLが少ないプロセスを1つ作る
                    fewest_host_now = tmp_list[-1][0]
                    make_fewest_host_proc_flag = True
                    if fewest_host is not None:
                        if fewest_host in hostName_process:
                            if hostName_process[fewest_host].is_alive():   # 既に一番待機URLが少ないサーバをクローリング中
                                make_fewest_host_proc_flag = False
                    if make_fewest_host_proc_flag:
                        make_process(fewest_host_now, setting_dict)
                        num_of_runnable_process -= 1
                        fewest_host = fewest_host_now

                    # 待機URLが多い順に作る
                    for host_url_list_tuple in tmp_list:   # tmp_listの各要素は、 (ホスト名, remaining辞書)のタプル
                        if num_of_runnable_process <= 0:
                            break
                        if host_url_list_tuple[0] in hostName_process:
                            if hostName_process[host_url_list_tuple[0]].is_alive():
                                continue   # プロセスが活動中なら、次に多いホストを
                        make_process(host_url_list_tuple[0], setting_dict)
                        num_of_runnable_process -= 1

        # メインループを抜け、結果表示＆保存
        remaining = len(url_list) + sum([len(dic['URL_list']) for dic in hostName_remaining.values()])
        current_achievement = get_achievement_amount()
        print('\nmain : -------------result------------------')
        print('main : assignment_url_set = ' + str(len(assignment_url_set)))
        print('main : current achievement = ' + str(current_achievement))
        print('main : all achievement = ' + str(all_achievement))
        print('main : number of child-process = ' + str(len(hostName_achievement)))
        run_time = int(time()) - current_start_time
        print('run time = ' + str(run_time))
        print('remaining = ' + str(remaining))
        w_file('result.txt', 'assignment_url_set = ' + str(len(assignment_url_set)) + '\n' +
               'current achievement = ' + str(current_achievement) + '\n' +
               'all achievement = ' + str(all_achievement) + '\n' +
               'number of child-process = ' + str(len(hostName_achievement)) + '\n' +
               'run time = ' + str(run_time) + '\n' +
               'remaining = ' + str(remaining) + '\n' +
               'date = ' + datetime.now().strftime('%Y/%m/%d, %H:%M:%S') + '\n', mode="a")

        print('main : save...')   # 途中結果を保存する
        copytree(org_path + '/RAD', 'TEMP')
        print('main : save done')

        if setting_dict['machine_learning']:
            print('main : wait for machine learning process')
            machine_learning_q['recv'].put('end')       # 機械学習プロセスに終わりを知らせる
            if not machine_learning_q['process'].join(timeout=60):  # 機械学習プロセスが終わるのを待つ
                print("main : Terminate machine-learning proc.")
                machine_learning_q['process'].terminate()
        if setting_dict['screenshots_svc']:
            print('main : wait for screenshots learning process')
            screenshots_svc_q['recv'].put('end')       # 機械学習プロセスに終わりを知らせる
            if not screenshots_svc_q['process'].join(timeout=60):  # 機械学習プロセスが終わるのを待つ
                print("main : Terminate screenshots-svc proc.")
                screenshots_svc_q['process'].terminate()
        if setting_dict['clamd_scan']:
            print('main : wait for clamd process')
            clamd_q['recv'].put('end')        # clamdプロセスに終わりを知らせる
            if not clamd_q['process'].join(timeout=60):   # clamdプロセスが終わるのを待つ
                print("main : Terminate clamd proc.")
                clamd_q['process'].terminate()
        print('main : wait for summarize alert process')
        summarize_alert_q['recv'].put('end')  # summarize alertプロセスに終わりを知らせる
        if not summarize_alert_q['process'].join(timeout=60):  # summarize alertプロセスが終わるのを待つ
            print("main : Terminate summarize-alert proc.")
            summarize_alert_q['process'].terminate()

        url_db.close()
        # メインループをもう一度回すかどうか
        if save:
            print('main : Restart...')
            run_count += 1
            os.chdir('..')
        else:
            os.chdir('..')
            break

    print('main : End')
