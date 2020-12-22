from __future__ import annotations

import json
import os
import pickle
import threading
import urllib.error
from copy import deepcopy
from datetime import datetime
from logging import getLogger
from multiprocessing import Queue, cpu_count
from time import sleep, time
from typing import Any, Dict, List, Tuple, Union, cast

import psutil
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait

from check_allow_url import inspection_url_by_filter
from checkers.mecab import (add_word_dic, get_tf_dict_by_mecab,
                            get_top10_tfidf, make_tfidf_dict)
from dealwebpage.inspection_page import (
    form_inspection, get_meta_refresh_url, iframe_inspection,
    meta_refresh_inspection, script_inspection)
from dealwebpage.robotparser import RobotFileParser
from dealwebpage.urldict import UrlDict
from dealwebpage.webpage import Page
from utils.alert_data import Alert
from utils.file_rw import r_file, w_file
from utils.location import location
from utils.logger import worker_configurer
from utils.sys_command import kill_chrome
from webdrivers.resources_observer import (cpu_checker, get_family,
                                           memory_checker)
from webdrivers.use_browser import (configure_logger, create_blank_window,
                                    get_window_url, quit_driver, set_html,
                                    take_screenshots)
from webdrivers.use_extentions import (configure_logger_for_use_extentions,
                                       rm_other_than_watcher,
                                       start_watcher_and_move_blank,
                                       stop_watcher_and_get_data)
from webdrivers.webdriver_init import get_fox_driver

html_special_char: List[Tuple[str, ...]] = list()  # URLの特殊文字を置換するためのリスト

dir_name: str = ''   # このプロセスの作業ディレクトリ
f_name: str = ''     # このプロセスのホスト名をファイル名として使えるように変換したもの
org_path: str = ""   # 組織のディレクトリ絶対パス

parser_threadId_set = set()                     # パーサのスレッドid集合 TODO: 消せる変数
parser_threads: Dict[int, Dict[str, Any]] = dict() # スレッドid : 実行時間
parser_thread_lock = threading.Lock()           # スレッド集合更新用ロック
num_of_pages: int = 0                           # 取得してパースした重複なしページ数. リダイレクト後が外部URL, エラーだったURLを含まない
num_of_files: int = 0                           # 取得してパースした重複なしファイル数. リダイレクト後に外部になるURL, エラーだったURLは含まない
url_cache = set()                               # 接続を試したURL集合. 他サーバへのリダイレクトURL含む. プロセスが終わっても消さずに保存
url_dict: UrlDict = UrlDict('')                   # サーバ毎のurl_dictの辞書を扱うクラス
robots = None                                   # robots.txtを解析するクラス
user_agent = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'

word_idf_dict: dict[str, int] = dict()  # 前回にこのサーバに出てきた単語とそのidf値
word_df_dict: dict[str, int] = dict()   # 今回, このサーバに出てきた単語と出現ページ数
word_df_lock = threading.Lock()         # word_df_dict更新の際のlock
iframe_src_set = set()                  # iframeのsrc先urlの集合
iframe_src_set_pre = set()              # 前回までのクローリング時のやつ
iframe_src_set_lock = threading.Lock()  # これは更新をcrawlerスレッド内で行うため排他制御しておく
script_src_set = set()                  # scriptのsrc先urlの集合
script_src_set_pre = set()              # 前回までのクローリング時のやつ
script_src_set_lock = threading.Lock()  # これは更新をcrawlerスレッド内で行うため排他制御しておく
request_url_set = set()                 # 各ページを構成するためにGETしたurlのネットワーク名の集合
request_url_filter: Dict[str, List[str]] = dict()             # 前回までのクローリング時のやつ
link_set = set()                        # ページに貼られていたリンク先URLのネットワーク名の集合
link_set_lock = threading.Lock()        # これは更新をcrawlerスレッド内で行うため排他制御しておく
link_url_filter: Dict[str, List[str]] = dict()                # 前回までのクローリング時のやつ
frequent_word_list: List[str] = list()  # 前回までこのサーバに出てきた頻出単語top50

# {file名 : [文字, 内容, ...], file名 : []...}
write_file_to_hostdir: Dict[str, List[Any]]= dict()    # server/ホスト名/の中に作るファイルの内容。{file名 : [文字, 内容, ...], file名 : []}
wfth_lock = threading.Lock()                           # write_file_to_hostdir更新の際のlock
write_file_to_resultdir: Dict[str, List[Any]] = dict() # result/result_*/の中に作るファイルの内容。{file名 : [内容, 内容, ...], file名 : []}
wftr_lock = threading.Lock()                           # write_file_to_maindir更新の際のlock
write_file_to_alertdir: List[Alert] = list()           # result/alert/の中に作るファイルの内容
wfta_lock = threading.Lock()                           # write_file_to_alertdir更新の際のlock

resource_dict: Dict[str, List[Union[List[Union[str, float]], List[Union[str, int]]]]] = dict()  # 資源使用率調査用
resource_dict["CPU"] = list()  # CPU使用率調査用
resource_dict["MEM"] = list()  # Memory使用率調査用
resource_terminate_flag = False
check_resource_threadId_set = set()

# ひとつのホストを回り続ける最大時間
LIMIT_TIME = 60 * 5

logger = getLogger(__name__)

def init(host: str, screenshots: bool):
    """
    クローラ初期設定
    - URL置換文字辞書の作成
    - 検査対象ホストの検査結果格納用ディレクトリ作成
    - これまでのクローリングデータを取得
      - request_url_filter
        - request url のホワイトリストのフィルタ
      - link_url_filter
        - リンクURLのホワイトリストのフィルタ
      - iframe_src_set_pre
        - これまでに集めたこの組織の全iframeタグのsrc値
      - script_src_set_pre
        - これまでに集めたこの組織の全scriptタグのsrc値をロード
      - frequent_word_list
        - これまでに集めた頻出単語をロード
      - word_idf_dict
        - idf辞書
      - word_df_dict
        - df辞書

    実行ディレクトリ:
        organization/<>/result/result_*/

    args:
        host: 検査対象ホスト名
        screenshots: スクリーンショットを撮る
    """
    global html_special_char, script_src_set, script_src_set_pre, robots, frequent_word_list
    global dir_name, f_name, word_idf_dict, word_df_dict, url_cache, url_dict, num_of_files, num_of_pages
    global request_url_set, request_url_filter, iframe_src_set, iframe_src_set_pre, link_set, link_url_filter

    # このファイル位置の絶対パスで取得 「*/src」
    src_dir = os.path.dirname(os.path.abspath(__file__))

    # URLにおける特殊文字置換用データ読み出し
    data_temp: str = r_file(src_dir + '/files/HTML_SPECHAR.txt') # type: ignore
    data_temp: List[str] = data_temp.split('\n') # type: ignore
    for line in data_temp:
        line = line.split('\t')
        html_special_char.append(tuple(line))
    html_special_char.append(('\r', ''))
    html_special_char.append(('\n', ''))

    # organization/<>/result/result_*/ にserverを作成
    if not os.path.exists('server'):
        os.mkdir('server')

    # ディレクトリ名の作成
    dir_name = host.replace(':', '-')

    # ファイル名を作成
    f_name = dir_name.replace('.', '-')
    if not os.path.exists('server/' + dir_name):
        os.mkdir('server/' + dir_name)

    if screenshots:
        if not os.path.exists(org_path + '/RAD/screenshots/' + dir_name):
            os.mkdir(org_path + '/RAD/screenshots/' + dir_name)
    os.chdir('server/' + dir_name)

    # 途中保存をロード
    if os.path.exists(org_path + '/RAD/temp/progress_' + f_name + '.pickle'):
        logger.debug("Loading past data... /RAD/temp/progress_%s.pickle", f_name)
        with open(org_path + '/RAD/temp/progress_' + f_name + '.pickle', 'rb') as f:
            data_temp: Dict[str, Any] = pickle.load(f)
            num_of_pages = data_temp['num_pages']
            num_of_files = data_temp['num_files']
            url_cache = deepcopy(data_temp['cache'])
            request_url_set = deepcopy(data_temp['request'])
            iframe_src_set = deepcopy(data_temp['iframe'])
            script_src_set = deepcopy(data_temp['script'])
            robots = data_temp['robots']
            link_set = deepcopy(data_temp['link'])
        logger.debug("Loading past data... FIN!")

    # robots.txtがNoneのままだった場合
    if robots is None:
        robots = RobotFileParser(url='http://' + host + '/robots.txt')
        try:
            robots.read()
        except urllib.error.URLError:   # サーバに接続できなければエラーが出る。
            robots = None               # robots.txtがなかったら、全てTrueを出すようになる。
        except Exception as err:
            # エラーとして, http.client.RemoteDisconnected などのエラーが出る
            # 'utf-8' codec can't decode byte (http://ritsapu-kr.com/)
            logger.exception(f'Exception occur: {err}')
            robots = None

    # request url のホワイトリストのフィルタをロード
    path = org_path + '/ROD/request_url/filter.json'
    if os.path.exists(path):
        with open(path, 'r') as f:
            request_url_filter = json.load(f)
    else:
        logger.debug("Not exist '/ROD/request_url/filter.json'")

    # リンクURLのホワイトリストのフィルタをロード
    path = org_path + '/ROD/link_url/filter.json'
    if os.path.exists(path):
        with open(path, 'r') as f:
            link_url_filter = json.load(f)
    else:
        logger.debug("Not exist '/ROD/link_url/filter.json'")

    # 今までのクローリングで集めた、この組織の全iframeタグのsrc値をロード
    path = org_path + '/ROD/iframe_url/matome.json'
    if os.path.exists(path):
        with open(path, 'r') as f:
            data_temp = json.load(f)
            iframe_src_set_pre = set(data_temp)
    else:
        logger.debug("Not exist '/ROD/iframe_url/matome.json'")

    # 今までのクローリングで集めた、この組織の全scriptタグのsrc値をロード
    path = org_path + '/ROD/script_url/matome.json'
    if os.path.exists(path):
        with open(path, 'r') as f:
            data_temp = json.load(f)
            script_src_set_pre = set(data_temp)
    else:
        logger.debug("Not exist '/ROD/script_url/matome.json'")

    # 今までのクローリングで集めた、このサーバの頻出単語をロード
    path = org_path + '/ROD/frequent_word_100/' + f_name + '.json'
    if os.path.exists(path):
        with open(path, 'r') as f:
            data_temp = json.load(f)
            frequent_word_list = list(data_temp)
    else:
        logger.debug("Not exist '/ROD/frequent_word_100/%s.json'", f_name)

    # idf辞書をロード
    path = org_path + '/ROD/idf_dict/' + f_name + '.json'
    if os.path.exists(path):
        logger.debug("Loading past 'idf_dict'...")
        if os.path.getsize(path) > 0:
            with open(path, 'r') as f:
                word_idf_dict = json.load(f)
        logger.debug("Loading past 'idf_dict'... FIN!")

    # df辞書をロード
    path = org_path + '/RAD/df_dict/' + f_name + '.pickle'
    if os.path.exists(path):
        logger.debug("Loading past 'df_dict'...")
        if os.path.getsize(path) > 0:
            with open(path, 'rb') as f:
                word_df_dict = pickle.load(f)
        logger.debug("Loading past 'df_dict'... FIN!")

    url_dict = UrlDict(f_name, org_path)
    copy_flag = url_dict.load_url_dict()
    if copy_flag:
        logger.debug("create 'notice.txt'")
        w_file('../../notice.txt', host + ' : ' + copy_flag + '\n', mode="a")

    # CPUやメモリの使用率データをロード
    key_list = ["CPU", "MEM"]
    for key in key_list:
        logger.debug("Loading past 'result/%s/%s.pickle'...", key, f_name)
        if os.path.exists("{}/result/{}/{}.pickle".format(org_path, key, f_name)):
            with open("{}/result/{}/{}.pickle".format(org_path, key, f_name), "rb") as f:
                resource_dict[key] = pickle.load(f)
        logger.debug("Loading past 'result/%s/%s.pickle'...FIN!", key, f_name)


def save_result(alert_process_q: Queue[Union[Alert, str]]):
    """
    クローリングして得たページの情報を外部ファイルに記録
    (url_dict, word_df_dict, num_pages, chache, request, robots, num_files, iframe, link, script)

    実行ディレクトリ: result/result_*/server/

    args:
        alert_process_q: 
    """
    url_dict.save_url_dict()
    if word_df_dict:
        logger.debug('%s: word_df_dict exist', f_name)
        path = org_path + '/RAD/df_dict/' + f_name + '.pickle'
        with open(path, 'wb') as f:
            logger.debug('%s: load word_df_dict', f_name)
            pickle.dump(word_df_dict, f)
    else:
        logger.debug('%s: word_df_dict not exist', f_name)
    if num_of_pages + num_of_files:
        with open(org_path + '/RAD/temp/progress_' + f_name + '.pickle', 'wb') as f:
            pickle.dump({'num_pages': num_of_pages, 'cache': url_cache, 'request': request_url_set, 'robots': robots,
                         "num_files": num_of_files, 'iframe': iframe_src_set, 'link': link_set,
                         'script': script_src_set}, f)
    w_file('achievement.txt', "{},{}".format(num_of_pages, num_of_files), mode="w")
    logger.debug("save %s's achievement.txt", f_name)

    # result_*/server/ホスト名/の中にファイルを確認
    # write_file_to_hostdir: {file名 : [文字, 内容, ...], file名 : []...}
    for file_name, value in write_file_to_hostdir.items():
        text = ''
        for i in value:
            if type(i) == list:
                if not os.path.exists(file_name):
                    text += i[0] + '\n'
                text += i[1] + '\n'
            else:
                text += i + '\n'
        w_file(file_name, text, mode="a")
        logger.debug("%s: save %s", f_name, file_name)

    for file_name, value in write_file_to_resultdir.items():
        text = ''
        for i in value:
            if type(i) == list:
                if not os.path.exists('../../' + file_name):
                    text += i[0] + '\n'
                text += i[1] + '\n'
            else:
                text += i + '\n'
        if 'falsification.cysec.cs.ritsumei.ac.jp' in dir_name:
            # 偽サイトの結果ファイルはresultディレに書かない
            w_file(file_name, text, mode="a")
            logger.debug("%s: save %s", f_name, file_name)
        else:
            # ex: new_page.csv, invisible_iframe.csv, script_name.csv を保存する
            w_file('../../' + file_name, text, mode="a")
            logger.debug("%s: save %s", f_name, file_name)

    # アラートディレクトリに保存するデータをalert出力専用プロセスに送信
    for data_dict in write_file_to_alertdir:
        alert_process_q.put(data_dict)

    key_list = ["CPU", "MEM"]
    for key in key_list:
        if not os.path.exists(org_path + "/result/" + key):
            os.mkdir(org_path + "/result/" + key)
        with open("{}/result/{}/{}.pickle".format(org_path, key, f_name), "wb") as f:
            pickle.dump(resource_dict[key], f)
        logger.debug('%s: save %s', f_name, key)


def update_write_file_dict(dic_type: str, key: str, content: Any):
    """
    クローリング結果をこのプロセス終了時に一気に書き込む処理用の一時変数に値を保存する関数  
    dic_typeによって、出力ファイルの保存場所が変化
    - "host"
      - organization/ritsumeikan/result/result_*/server/各ホスト名/の中
    - "result"
      - organization/ritsumeikan/result/result_*/の中
    警告を表すalertディレクトリに書き出す場合専用のプロセスを用いる -> summaraize_alert.py
    alertディレクトリに書き出す内容は、write_file_to_alertdirというリストに保存しておき、
    save_result()で、専用のプロセスに送信する

    args:
        dic_type: "host", "result"
        key: ファイル名
        content: ファイルに入れる内容(csvファイルなら: [ヘッダ, 内容], その他: textファイル)
    """

    # マルチスレッドの中から呼び出されることもあるため、排他制御
    # lock = None
    dic = None
    # どのフォルダに保存するファイルか選択
    if dic_type == 'host':
        dic = write_file_to_hostdir
        lock = wfth_lock
    else:
        # elif dic_type == 'result':
        dic = write_file_to_resultdir
        lock = wftr_lock
    # 各辞書は、ファイル名：[内容, 内容, ...]になるように
    # alertDirだけ、ファイル名：[辞書, 辞書, ...]  (summarize_alertプロセスに渡すため)
    with lock:
        if key.endswith('.csv'):
            # csvファイルの場合、contentはリストで[ヘッダ, 内容]となっている
            if key not in dic:
                # 初回はヘッダを含めて書き込み
                dic[key] = [content]
            else:
                # 1行目以降は、内容だけ入れる
                dic[key].append(content[1])
        else:
            # textファイルの場合
            if key not in dic:
                dic[key] = [content]
            else:
                dic[key].append(content)


def send_to_parent(sendq: Queue[Union[str, Dict[str, Any], Tuple[str, ...]]], data: Union[str, Dict[str, Any], Tuple[str, ...]]):
    """
    親プロセス(main.py)に自身が担当しているサイトのURLを要求する
    親からのデータは q_recv に入れられる
    """
    if not sendq.full():
        sendq.put(data)  # 親にdataを送信
    else:
        sleep(1)
        sendq.put(data)


def parser(parse_args_dic: Dict[str, Any]):
    global word_df_dict
    host: str = parse_args_dic['host']
    page: Page = parse_args_dic['page']
    q_send = parse_args_dic['q_send']
    file_type = parse_args_dic['file_type']
    # machine_learning_q = parse_args_dic['machine_learning_q']
    use_mecab = parse_args_dic['use_mecab']
    # screenshots_svc_q = parse_args_dic['screenshots_svc_q']
    # TODO: 画像の保存
    # img_name = parse_args_dic['img_name']
    nth = parse_args_dic['nth']
    filtering_dict = parse_args_dic["filtering_dict"]
    if "falsification.cysec" in host:
        logger.info("start parse : URL=%s", page.url)

    # スクレイピングするためのsoup
    try:
        # ここで以下のエラーが出るが、soup自体は取得できていて、soup.prettify()もできたので無視する
        # encoding error : input conversion failed due to input error,
        soup = BeautifulSoup(page.html, 'lxml')
    except Exception:
        soup = BeautifulSoup(page.html, 'html.parser')

    # htmlソースからtagだけ取り出して機械学習に入れる(今はしていない)
    # get_tags_from_html(soup, page, machine_learning_q)

    # ページに貼られているリンク集を作り、親プロセスへ送信
    if file_type == 'xml':
        page.make_links_xml(soup)   # xmlページのリンク抽出
    elif file_type == 'html':
        page.make_links_html(soup)  # htmlページのリンク抽出
    page.complete_links(html_special_char)    # pageのリンク集のURLを補完する

    # 未知サーバのリンクが貼られていないかをチェック
    result_set = set()
    if page.normalized_links:
        with link_set_lock:  # リンク集合の更新
            link_set.update(page.normalized_links)
        # フィルタを通してURLを判定
        normalize_links = page.normalized_links
        result_set = inspection_url_by_filter(url_list=normalize_links, filtering_dict=filtering_dict,
                                              special_filter=link_url_filter)
        # 検査結果がFalse(組織外)、もしくは"Unknown"(不明)だったURLを外部ファイルに出力
        strange_set = set([result[0] for result in result_set if (result[1] is False) or (result[1] == "Unknown")])
        if strange_set:
            content = str(strange_set)[1:-1].replace(" ", "").replace("'", "").replace(',', ' ')
            with wfta_lock:
                write_file_to_alertdir.append(Alert(
                    url = page.url_initial,
                    file_name ='link_to_new_server.csv',
                    content = content,
                    label = 'InitialURL, URL, LINK'
                ))

    # 組織内かどうかをチェックしたリンクURLをすべて親に送信
    send_data = {'type': 'links', 'url_set': result_set, "url_src": page.url}   # 親に送るデータ
    send_to_parent(q_send, send_data)    # 親にURLリストを送信

    # 検査
    # 前回とのハッシュ値を比較
    num_of_days, _ = url_dict.compere_hash(page)
    # int型: ハッシュ値が違う。
    # True : 変化なし
    # False: 新規ページ
    # None : どこかでエラー。
    if type(num_of_days) == int:
        update_write_file_dict('result', 'change_hash_page.csv',
                               content=['URL,num of no-change days', page.url + ', ' + str(num_of_days)])
    elif num_of_days is True:
        update_write_file_dict('result', 'same_hash_page.csv', content=['URL', page.url])
    elif num_of_days is False:
        update_write_file_dict('result', 'new_page.csv', content=['URL,src', page.url + ', ' + page.src])
        page.new_page = True

    if use_mecab:
        # このページの各単語のtf値を計算、df辞書を更新
        hack_level, word_tf_dict = get_tf_dict_by_mecab(soup)  # tf値の計算と"hacked by"検索
        if hack_level:    # hackの文字が入っていると0以外が返ってくる
            if hack_level == 1:
                update_write_file_dict('result', 'hack_word_Lv' + str(hack_level) + '.txt', content=page.url)
            else:
                # "hacked"が文章に含まれていると外部ファイルに保存
                with wfta_lock:
                    write_file_to_alertdir.append(Alert(
                        url       = page.url_initial,
                        file_name = 'hack_word_Lv' + str(hack_level) + '.csv',
                        content   = page.url_initial + ", " + page.url + ', ' + page.src,
                        label     = 'InitialURL, URL, SOURCE'
                    ))
        if word_tf_dict is not False:
            word_tf_dict = cast(Dict[str, float], word_tf_dict)
            with word_df_lock:
                word_df_dict = add_word_dic(word_df_dict, word_tf_dict)  # サーバのidf計算のために単語と出現ページ数を更新

            # 前回のクローリング結果から計算したidf辞書があれば、重要単語を抽出
            if word_idf_dict:
                word_tfidf = make_tfidf_dict(idf_dict=word_idf_dict, tf_dict=word_tf_dict)  # tf-idf値を計算
                top10 = get_top10_tfidf(tfidf_dict=word_tfidf, nth=nth)   # top10を取得。ページ内に単語がなかった場合は空リストが返る
                # ハッシュ値が異なるため、重要単語を比較
                # if num_of_days is not True:
                if True:  # 実験のため毎回比較
                    pre_top10 = url_dict.get_top10_from_url_dict(url=page.url)    # 前回のtop10を取得
                    if pre_top10 is not None:
                        symmetric_difference = set(top10) ^ set(pre_top10)         # 排他的論理和
                        if len(symmetric_difference) > ((len(top10) + len(pre_top10)) * 0.8):
                            with wfta_lock:
                                write_file_to_alertdir.append(Alert(
                                    url       = page.url_initial,
                                    file_name ='change_important_word.csv',
                                    content   = page.url_initial + ", " + page.url + ', ' \
                                                  + str(top10)[1:-1] + ', ,' + str(pre_top10)[1:-1],
                                    label     = 'InitialURL, URL, TOP10, N/A, PRE'
                                ))
                        update_write_file_dict('result', 'symmetric_diff_of_word.csv',
                                               content=['URL,length,top10,pre top10', page.url + ', ' +
                                                        str(len(symmetric_difference)) + ', ' + str(top10)[1:-1] + ', ,'
                                                        + str(pre_top10)[1:-1] + ', ' + str(num_of_days)])
                url_dict.add_top10_to_url_dict(url=page.url, top10=top10)   # top10を更新

            # ページにあった単語が今までの頻出単語にどれだけ含まれているか調査-------------------------------
            if frequent_word_list:
                n = 50
                # 上位50個と比較し、頻出単語に含まれていなかった単語の数を保存
                # (frequent_word_listには、サイトの頻出単語が上位100個まで保存されているが、50個で十分と判断)
                max_num = min(len(frequent_word_list), n)  # 保存されている単語数がn個未満のサーバがあるため
                and_set = set(word_tf_dict.keys()).intersection(set(frequent_word_list[0:max_num]))

                # このページにある単語から頻出単語リストの単語を引き、その数を調べる
                diff_set = set(word_tf_dict.keys()).difference(set(frequent_word_list[0:max_num]))
                update_write_file_dict('result', 'and_diff_of_word_in_new_page.csv',
                                       ['URL,and,diff,per', page.url + ', ' + str(len(and_set)) + ', ' +
                                        str(len(diff_set)) + ', ' + str(len(diff_set)/len(word_tf_dict.keys()))])

                # 新しく見つかったURLで、ANDの単語(このページの単語と今までの頻出単語top50とのAND)が5個以下なら
                if len(and_set) < 6 and page.new_page:
                    with wfta_lock:
                        write_file_to_alertdir.append(Alert(
                            url       = page.url_initial,
                            file_name = 'new_page_without_frequent_word.csv',
                            content   = page.url_initial + ", " + page.url + ', ' + str(and_set),
                            label     = 'InitalURL, URL, WORDS'
                        ))

    # iframeの検査
    iframe_result = iframe_inspection(soup)     # iframeがなければFalse
    if iframe_result:
        iframe_result = cast(Dict[str, List[str]], iframe_result)
        if iframe_result['iframe_src_list']:    # iframeのsrcURLのリストがあれば
            with iframe_src_set_lock:   # 今回見つかったiframeのsrc集合の更新
                iframe_src_set.update(set(iframe_result['iframe_src_list']))
            if iframe_src_set_pre:   # 前回のクローリング時のiframeのsrcデータがあれば
                diff = set(iframe_result['iframe_src_list']).difference(iframe_src_set_pre)   # 差をとる
                if diff:   # 前回のクローリング時に確認されなかったURLのiframeが使われているならば
                    with wfta_lock:
                        write_file_to_alertdir.append(Alert(
                            url       = page.url_initial,
                            file_name = 'new_iframeSrc.csv',
                            content   = page.url_initial + ", " + page.url + ", " + str(diff)[1:-1],
                            label     = 'InitialURL, URL, iframe_src'
                        ))
        # 目に見えないiframeがあるか。javascriptを動かすためのiframeが結構見つかる。
        if iframe_result['invisible_iframe_list']:
            update_write_file_dict('result', 'invisible_iframe.csv', content=['URL', page.url])

    # meta Refreshの検査
    # http-equivがrefreshのタグのリスト取ってくる(なければFalse)
    meta_refresh_result = meta_refresh_inspection(soup)
    if meta_refresh_result:
        meta_refresh_result = cast(List[ResultSet], meta_refresh_result)
        meta_refresh = ''
        for i in meta_refresh_result:
            meta_refresh += str(i) + ','
        update_write_file_dict('result', 'meta_refresh.csv', content=['URL, meta-ref', page.url + ', ' + meta_refresh])
        meta_refresh_list = get_meta_refresh_url(meta_refresh_result, page)   # refreshタグからURLを抽出
        # 親にURLを送信する。リダイレクトと同じ扱いをするため、複数あっても(そんなページ怪しすぎるが)１つずつ送る
        result_set = inspection_url_by_filter(url_list=meta_refresh_list, filtering_dict=filtering_dict)
        while result_set:
            send_to_parent(q_send, {'type': 'redirect', 'url_set': [result_set.pop()], "url_src": page.src,
                                    "ini_url": page.url_initial})

    # scriptの検査
    # script名が特徴的かどうか。[(スクリプト名, そのスクリプトタグ),()...]となるリストを返す
    script_result = script_inspection(soup=soup)
    if script_result:
        script_result = cast(Dict[str, List[Tuple[str, str]]], script_result)
        # 怪しいscript名があるか
        if script_result['suspicious_script_name']:
            for suspicious_name, suspicious_script in script_result['suspicious_script_name']:
                update_write_file_dict('result', 'script_name.csv',
                                       content=['script name,URL,script', suspicious_name + ',' + page.url + ',' +
                                                suspicious_script])
        # タイトルにscriptが含まれているかどうか
        if script_result['script_in_title']:
            update_write_file_dict('result', 'script_in_title.csv',
                                   content=['URL', page.url, str(script_result['script_in_title'])])
        # 前回のクローリングで見つかっていないscriptのsrcがあるか
        if script_result['script_src_list']:    # scriptのsrcURLのリストがあれば
            with script_src_set_lock:   # 今回見つかったscriptのsrc集合の更新
                script_src_set.update(set(script_result['script_src_list']))
            if script_src_set_pre:   # 前回のクローリング時のscriptのsrcデータがあれば
                diff = set(script_result['script_src_list']).difference(script_src_set_pre)   # 差をとる
                if diff:   # 前回のクローリング時に確認されなかったURLがscriptに使われているならば
                    with wfta_lock:
                        write_file_to_alertdir.append(Alert(
                            url       = page.url_initial,
                            file_name = 'new_scriptSrc.csv',
                            content   = page.url_initial + ", " + page.url + ", " + str(diff)[1:-1],
                            label     = 'InitialURL, URL, script_src',
                        ))

    # formの検査
    form_result = form_inspection(soup=soup)
    if form_result:
        form_result = cast(Dict[str, List[str]], form_result)
        # formのaction先が未知のサーバかどうか
        url_list = form_result["form_action"]
        # URLを正規化
        url_list_temp: set[str] = set()
        for url in url_list:
            if not (url.startswith('http')):
                url = page.comp_http(page.url, url)
                if url == '#':  # 'javascript:'から始まるものや'#'から始まるもの
                    continue
            url_list_temp.add(url)
        # リンクURLのフィルタに通す(本当はformURL専用のホワイトリストを作成するべきだが、時間がなかった)
        result_set = inspection_url_by_filter(url_list=url_list_temp, filtering_dict=filtering_dict,
                                              special_filter=link_url_filter)
        # リンクURLのフィルタを通した結果、False(組織外)もしくは"Unknown"(不明)だったものを
        strange_set = set([result[0] for result in result_set if (result[1] is False) or (result[1] == "Unknown")])
        if strange_set:
            # 次はリクエストURLのフィルタに通す
            result_set = inspection_url_by_filter(url_list=strange_set, filtering_dict=filtering_dict,
                                                  special_filter=request_url_filter)
            # ２つのフィルタを通しても未知のサーバだと判断されたらアラート
            strange_set = set([result[0] for result in result_set if (result[1] is False) or (result[1] == "Unknown")])
            if strange_set:
                content = str(strange_set)[1:-1].replace(" ", "").replace("'", "").replace(',', ' ')
                with wfta_lock:
                    write_file_to_alertdir.append(Alert(
                        url = page.url_initial,
                        file_name = 'new_form_url.csv',
                        content = page.url_initial + ", " + page.url + ", " + content,
                        label = 'InitialURL, URL, form_url'
                    ))

    # requestURL を url_dictに追加(ページをレンダリングする際のリクエストURLを、各ページごとに保存。しかし、何かに使っているわけではない。)
    if page.request_url:
        if url_dict:
            _ = url_dict.update_request_url_in_url_dict(page)
        else:
            logger.error("There are no url_dict")

    # # スレッド集合から削除して、検査終了
    # try:
    #     parser_threadId_set.remove(threading.get_ident())   # del_thread()で消されていた場合、KeyErrorになる
    #     del parser_threadId_time[threading.get_ident()]
    # except KeyError:
    #     logger.info(f"{host} thread was deleted by del_thread")
    #     pass
    # except Exception as err:
    #     logger.exception(f"Failed to del thread: {err}")
    #     pass


def check_thread_time():
    """
    180秒以上続いているparserスレッドのリストを返す
    """
    thread_list: List[int] = list()
    try:
        with parser_thread_lock:
            for threadId, thread_detail in parser_threads.items():
                if (int(time()) - thread_detail['time']) > 180:
                    thread_list.append(threadId)
    except RuntimeError as err:
        logger.exception(f'Exception occur: {err}')
    return thread_list


def del_thread(host: str):
    """
    5秒間隔でパーススレッドが生きているかを調べる
    終わっているならjoinしてリソースの回収

    TODO: 180秒以上かかっているならスレッドを強制終了したい
    """
    while True:
        del_thread: List[int] = list()
        sleep(5)
        # 正常に終了しているスレッドを回収する
        for threadId, thread_detail in parser_threads.items():
            if not thread_detail['thread'].is_alive():
                logger.debug('thread joined')
                thread_detail['thread'].join()
                del_thread.append(threadId)
                with parser_thread_lock:
                    parser_threadId_set.remove(threadId)
        with parser_thread_lock:
            for target in del_thread:
                del parser_threads[target]

        # 180秒以上続いているスレッドを強制削除したいが実際はできていない
        # thread を強制終了できるクラスに変更してterminateする必要がある
        # というかまずそんなパーススレッドができるとは思えない
        # まぁDAEMONにしてるしいいか...
        del_thread_list = check_thread_time()
        for th in del_thread_list:
            logger.critical('DEL_thread: %s deleted: %s', host, str(th))
            try:
                # 消去処理がパーススレッドとほぼ同時に行われるとなるかも？(多分ない)
                with parser_thread_lock:
                    parser_threadId_set.remove(th)
                    del parser_threads[th]
            except KeyError:
                logger.warning('KeyError occur')
            except Exception as err:
                logger.exception(f'Exception Occur: {err}')


def resource_observer_thread(args: Dict[str, Any]):
    """
    資源監視スレッド
    """
    global resource_terminate_flag, resource_dict
    t = threading.currentThread()
    cpu_limit: int = args["cpu"]
    memory_limit: int = args["mem"]
    cpu_num: int = args["cpu_num"]
    initial: str = args["initial"]
    src: str = args["src"]
    url: str = args["url"]
    pid: int = args["pid"]
    while getattr(t, "run", True):
        kill_flag = False
        family: List[psutil.Process] = get_family(pid)
        if "falsification" in url:
            logger.info("Resource check : %s", url)

        # CPU
        ret, ret2 = cpu_checker(family, limit=cpu_limit, cpu_num=cpu_num)
        if ret:
            logger.warning("HIGH CPU: URL=%s", url)
            for p_dict in ret:
                logger.warning("HIGH CPU: PROCESS = %s", p_dict["p_name"])
            proc_info = [(p_dict["p_name"], p_dict["cpu_per"]) for p_dict in ret]
            with wfta_lock:
                write_file_to_alertdir.append(Alert(
                    url       = initial,
                    file_name = 'over_work_cpu.csv',
                    content   = initial + ", " + url + ", " + src + ", " + str(proc_info)[1:-1],
                    label     = 'InitialURL, URL, Src, Info'
                ))
        # CPU使用率調査(ブラウザ関連プロセスの中で、一番CPU使用率が高かったものを記録)
        apdata = [url, max(ret2)]
        resource_dict["CPU"].append(apdata)

        # Memory
        ret, ret2 = memory_checker(family, limit=memory_limit)
        if ret:
            kill_flag = True
            logger.warning("HIGH MEM: URL=%s", url)
            for p_dict in ret:
                logger.warning("HIGH MEM: PROCESS = %s", p_dict["p_name"])
            proc_info = [(p_dict["p_name"], p_dict["mem_used"]) for p_dict in ret]
            with wfta_lock:
                write_file_to_alertdir.append(Alert(
                    url = initial,
                    file_name = 'over_work_memory.csv',
                    content = initial + ", " + url + ", " + src + ", " + str(proc_info)[1:-1],
                    label = 'InitialURL ,URL, Src, Info'
                ))
        # メモリ使用率調査(ブラウザ関連プロセスの中で、一番メモリ使用率が高かったものを記録)
        apdata = [url, max(ret2)]
        resource_dict["MEM"].append(apdata)

        # kill process's family with using much memory
        if kill_flag:
            resource_terminate_flag = True
            for p in family:
                logger.info("Terminate browser: URL=%s", url)
                try:
                    p.kill()
                except Exception as err:
                    logger.exception(f'Process terminate Error, {err}')
            break

        # このスレッドのidがcheck_resource_threadId_setから削除されていればbreak
        if threading.get_ident() not in check_resource_threadId_set:
            if "falsification.cysec.cs" in url:
                logger.info("Resource Check has completed : %s", url)
            break
    logger.debug("Finish resource_observer_thread")


def receive(recv_r: Queue[Union[str, Dict[str, str]]]) -> Any:
    """
    5秒間受信キューに何も入っていなければFalseを返す
    送られてくるのは、(URL, src) or 'nothing'

    args:
        recv_r: 
    """

    try:
        temp_r = recv_r.get(block=True, timeout=5)
    except:
        logger.info(f"queue is Empty")
        return False
    return temp_r


def page_or_file(page: Page) -> Union[str, bool]:
    """
    ページの content_type を調査

    args:
        page: 調査中のPage情報
    return:
        文字列 or False
    """
    xml_types = ['plain/xml', 'text/xml', 'application/xml']
    html_types = ['html']

    if page.content_type:
        for xml in xml_types:
            if xml in page.content_type:
                return 'xml'
        for html_type in html_types:
            if html_type in page.content_type:
                return 'html'
        # 空白のままを含む不明な content_type ならば False
        logger.debug("Unkown content type: '%s'", page.content_type)
        return False
    else:
        # Content_type が None ならば
        return False


def check_redirect(page: Page, host: str):
    """
    リダイレクト先の調査
    - URLが変わっていなければFalse
    - リダイレクトしていても同じサーバ内ならば'same'
    - 違うサーバならTrue

    args:
        page:
        host:
    return:
        文字列 or bool
    """
    if page.url_initial == page.url:
        return False
    if host == page.hostName:
        return 'same'
    return True


def extract_extension_data_and_inspection(page: Page, filtering_dict: Dict[str, Any]):
    """
    拡張機能の専用ページから、拡張機能が集めたデータを取得し、検査
    """
    global request_url_set
    # Watcher.htmlをスクレイピングするためのsoup
    try:
        soup_3 = BeautifulSoup(page.watcher_html, 'lxml')
    except Exception:
        soup_3 = BeautifulSoup(page.watcher_html, 'html.parser')
    page.extracting_extension_data(soup_3)

    # # 別サーバにリダイレクトしていなければ、RequestURLにチェックをする
    # if check_redirect(page, host) is not True:
    # requestURLが取れていたら、フィルタを通して疑わしいリクエストがあればアラート
    if page.request_url:
        page_request_url = page.request_url
        request_url_set = request_url_set.union(page.request_url)
        result_set = inspection_url_by_filter(url_list=page_request_url, filtering_dict=filtering_dict,
                                              special_filter=request_url_filter)
        strange_set = set([result[0] for result in result_set if (result[1] is False) or (result[1] == "Unknown")])
        if strange_set:
            content = str(strange_set)[1:-1].replace(" ", "").replace("'", "").replace(',', ' ')
            with wfta_lock:
                write_file_to_alertdir.append(Alert(
                    url       = page.url_initial,
                    file_name = 'request_to_new_server.csv',
                    content   = page.url_initial + ", " + page.url + ", " + content,
                    label     = 'InitialURL,URL,request_url'
                ))

    # 自動downloadがあればアラート
    if page.download_info:
        for file_id, info in page.download_info.items():
            with wfta_lock:
                write_file_to_alertdir.append(Alert(
                    url       = page.url_initial,
                    file_name = 'download_url.csv',
                    content   = page.url_initial + ", " + file_id + ", " + info["StartTime"] + ", " + info["FileName"] \
                                + ", " + str(info["FileSize"]) + ", " + str(info["TotalBytes"]) + ", " + info["Mime"] \
                                + ", " + info["URL"] + ", " + info["Referrer"] + ", " + page.url,
                    label     = 'InitialURL, id, StartTime, FileName, FileSize, TotalBytes, Mime, URL, Referrer, FinalURL',
                ))

    # URL遷移の記録があれば、リンクのフィルタを通し、疑わしいURLを含んでいればアラート
    if page.among_url:
        among_url_set = set(page.among_url)
        result_set = inspection_url_by_filter(url_list=among_url_set, filtering_dict=filtering_dict,
                                              special_filter=link_url_filter)
        strange_set = set([result[0] for result in result_set if (result[1] is False) or (result[1] == "Unknown")])
        if strange_set:
            content = str(page.among_url)[1:-1].replace(" ", "").replace("'", "") + ",N/A," + \
                      str(strange_set)[1:-1].replace(" ", "").replace("'", "")
            with wfta_lock:
                write_file_to_alertdir.append(Alert(
                    url       = page.url_initial,
                    file_name = 'url_history.csv',
                    content   = page.url_initial + ", " + page.url + ', ' + page.src + ', ' + content,
                    label     = 'InitialURL, FinalURL, src, AmongURL, , StrangeURL',
                ))


def crawler_main(queue_log: Queue[Any], args_dic: dict[str, Any]):
    """
    接続間隔はurlopen接続後、ブラウザ接続後、それぞれ接続する関数内で１秒待機
    """
    global org_path, num_of_pages, num_of_files
    worker_configurer(queue_log, logger)

    logger.debug("crawler_main start")

    page = None
    error_break = False

    # 引数取り出し
    host: str = args_dic['host_name']
    q_recv: Queue[Any] = args_dic['parent_sendq']
    q_send: Queue[Any] = args_dic['child_sendq']
    clamd_q: Queue[Any] = args_dic['clamd_q']
    screenshots: bool = args_dic['screenshots']
    use_browser: bool = args_dic['headless_browser']
    use_mecab: bool = args_dic['mecab']
    alert_process_q: Queue[Union[Alert, str]] = args_dic['alert_process_q']
    nth: int = args_dic['nth']
    org_path = args_dic['org_path']
    filtering_dict: Dict[str, Any] = args_dic["filtering_dict"]

    if "falsification" in host:
        import sys
        f = open(host + ".log", "a")
        sys.stdout = f

    # ヘッドレスブラウザを使うdriverを取得、一つのクローリングプロセスは一つのブラウザを使う
    # TODO: ここが失敗している？Driverのエラーの原因はここらっぽい
    if use_browser:
        driver_info = get_fox_driver(queue_log, screenshots, user_agent=user_agent, org_path=org_path)
        if driver_info is False:
            logger.warning("%s : cannnot make browser process", host)
            sleep(1)
            kill_chrome("geckodriver")
            kill_chrome("firefox-bin")
            os._exit(0) # type: ignore

        driver_info = cast(Dict[str, Any], driver_info)
        driver: WebDriver = driver_info["driver"]
        watcher_window: Union[int, str] = driver_info["watcher_window"]
        wait: WebDriverWait = driver_info["wait"]
        configure_logger(queue_log)
        configure_logger_for_use_extentions(queue_log)

    # 保存データのロードや初めての場合は必要なディレクトリの作成などを行う
    init(host, screenshots)

    # 180秒以上パースに時間がかかるスレッドは削除する(ためのスレッド)...実際にそんなスレッドがあるかは不明
    t = threading.Thread(target=del_thread, args=(host,))
    t.daemon = True
    t.start()

    # 長時間回り続けるのを防ぐために一旦切るための
    start_time = time()

    # クローラプロセスメインループ
    while True:

        # 動いていることを確認
        if "falsification" in host:
            pid = os.getpid()
            if page is None:
                logger.info('%s (%d): main loop is running', host, pid)
            else:
                logger.info('%s (%d): %s : DONE', host, pid, page.url_initial)

        # 前回(一個前のループ)にクローリングしたURLを保存し、driverのクッキー消去
        if page is not None:
            url_cache.add(page.url_initial)   # 親プロセス(main.py)から送られてきたURL
            url_cache.add(page.url_urlopen)   # urlopenで得たURL
            url_cache.add(page.url)           # 最終的にパースしたURL(urlopenで得たURLとブラウザで得たURLは異なる可能性がある)
            page = None
            try:
                cookies: Any = driver.get_cookies()
                if len(cookies) > 0:
                    logger.debug(f"delete cookies: {cookies}")
                    driver.delete_all_cookies()   # クッキー削除
            except Exception as err:
                logger.exception(f'Fail to del cookies: {err}')
                pass
            # 前回のウェブページの資源監視スレッドを終わらす
            # 資源監視スレッドは、この集合(check_resource_threadId_set)に自身のスレッドIDがある場合は無限に資源監視を行うため、この集合をクリアする
            check_resource_threadId_set.clear()

        # クローリングするURLを取得
        send_to_parent(sendq=q_send, data='plz')   # 親プロセス(main.py)に自身が担当しているサイトのURLを要求
        search_tuple = receive(q_recv)
        if search_tuple is False:
            # 5秒間何も届かなければFalseが入っている
            logger.warning("%s: couldn't get data from main process.", host)
            # 実行中のパーススレッドが処理を終えると、クローラメインプロセスをbreakする
            while parser_threadId_set:
                logger.warning('%s: wait 3sec because the queue is empty.', host)
                sleep(3)
            break
        elif search_tuple == 'nothing':
            # このプロセスに割り当てるURLがないとき
            if "falsification" in host:
                logger.warning("%s: nothing!!!!!!!!!!!!!!!!!!!!!!", host)
            while parser_threadId_set:
                # 実行中のパーススレッドが処理を終えるまで待つ
                logger.debug('%s : wait 3sec for finishing parse thread', host)
                sleep(3)
            # 3秒待機後、親プロセスにURLをもう一度要求する
            sleep(3)
            send_to_parent(sendq=q_send, data='plz')   # plz要求
            search_tuple = receive(q_recv)             # 応答確認
            if type(search_tuple) is tuple:
                send_to_parent(q_send, 'receive')
            else:
                # ２回目もFalse or nothingだったらメインを抜ける
                break
        else:
            # クローリングするべきURLのタプルが来たとき
            if ("falsification" in host) or ("www.img.is.ritsumei.ac.jp" in host):
                logger.debug("%s : receive '%s'", host, str(search_tuple[0]))
            send_to_parent(q_send, 'receive')

        # 検索するURLを取得
        url, url_src = search_tuple  # 親から送られてくるURLは、(URL, リンク元URL)のタプル
        if url in url_cache:    # 既にクローリング済ならば次へ。
            continue           # ここでキャッシュに当てはまるのは、NOT FOUNDページにリダイレクトされた後のURLとか？

        # Pageオブジェクトを作成(robots.txtの確認の前に作成しておかないと、次のループの最初に済URL集合(url_cache)に保存されない)
        page = Page(url, url_src)

        # robots.txtがあれば、それに準拠する
        if robots is not None:
            if robots.can_fetch(useragent=user_agent, url=page.url) is False:
                continue
        if ("falsification" in host) or ("www.img.is.ritsumei.ac.jp" in host):
            logger.debug("get by urlopen: %s", page.url)

        logger.info("Try to Check %s", page.url)

        # urlopenで接続
        urlopen_result = page.set_html_and_content_type_urlopen(page.url, time_out=30)
        if type(urlopen_result) is list:  # listが返るとエラー
            urlopen_result = cast(list[str], urlopen_result)
            # URLがこのサーバの中でひとつ目じゃなかった場合、次のURLへ
            if num_of_pages + num_of_files:
                update_write_file_dict('host', urlopen_result[0]+'.txt', content=urlopen_result[1])
                continue
            # ひとつ目のURLだった場合、もう一度やってみる
            # これにアクセスできなかったら、そのサイトの全てのページを取得できない可能性があるため)
            logger.info("Retrying to first access server: %s", page.url)
            update_write_file_dict('host', urlopen_result[0]+'.txt', content=urlopen_result[1] + ', and try again')
            urlopen_result = page.set_html_and_content_type_urlopen(page.url, time_out=60)  # 次は90秒待機する
            if type(urlopen_result) is list:  # 二回目も無理なら諦める
                urlopen_result = cast(list[str], urlopen_result)
                logger.warning("Give up to access %s", url)
                update_write_file_dict('host', urlopen_result[0] + '.txt', content=urlopen_result[1])
                continue

        # リダイレクトのチェック
        redirect = check_redirect(page, host)
        if redirect is True:   # 別サーバへリダイレクトしていればTrue、親プロセス(main.py)にそのURLを送信して、次のURLへ
            page_url_set = set(page.url)
            result_set = inspection_url_by_filter(url_list=page_url_set, filtering_dict=filtering_dict)
            send_to_parent(q_send, {'type': 'redirect', 'url_set': result_set, "ini_url": page.url_initial,
                                    "url_src": page.src})
            continue
        if redirect == "same":    # 同じホスト内のリダイレクトの場合、処理の続行を親プロセスに通知
            send_to_parent(sendq=q_send, data=(page.url, "redirect"))

        # urlopenでurlが変わっている可能性があるため再度重複チェック
        if page.url in url_cache:
            continue

        # content-typeからウェブページ(str)かその他ファイル(False)かを判断
        file_type = page_or_file(page)
        if page.content_type:
            update_write_file_dict('host', 'content-type.csv', ['content-type,url,src', page.content_type.replace(',', ':')
                                                            + ', ' + page.url + ', ' + page.src])  # 記録
        else:
            update_write_file_dict('host', 'content-type.csv', ['content-type,url,src', 'NoneType,' + page.url + ',' + page.src]) # 記録
            logger.warning("Content-type is None: %s", page.url)

        if type(file_type) is str:   # ウェブページの場合
            # img_name = False
            logger.debug("%s is webpage", page.url)
            if use_browser:
                # ヘッドレスブラウザでURLに再接続。関数内で接続後１秒待機
                # robots.txtを参照
                # watcher window以外を消す
                watcher_window = cast(Union[int, str], watcher_window)
                watcher_window = rm_other_than_watcher(driver, wait, watcher_window)
                if robots is not None:
                    if robots.can_fetch(useragent=user_agent, url=page.url) is False:
                        continue
                # ページをロードするためのabout:blankのwindowを作る
                logger.debug('creating blank_window...')
                blank_window = create_blank_window(driver=driver, wait=wait, watcher_window=watcher_window)
                if blank_window is False:
                    logger.debug('Failed to create blank...')
                    error_break = True
                    break
                logger.debug('creating blank_window... FIN!')
                blank_window = cast(str, blank_window)
                # watchingを開始し、ブランクページに移動する(URLに接続する準備完了)
                logger.debug('start watcher and move to blank...')
                re = start_watcher_and_move_blank(driver=driver, wait=wait, watcher_window=watcher_window,
                                                  blank_window=blank_window)
                if re is False:
                    logger.debug('Filed to move blank...')
                    error_break = True
                    break
                logger.debug('start watcher and move to blank... FIN')

                # ヘッドレスブラウザのリソース使用率を監視するスレッドを作る
                # os.getpid(): 現在のプロセスidを返す
                args = {"src": page.src, "url": page.url, "initial": page.url_initial, "cpu": 60,
                        "cpu_num": cpu_count(), "mem": 2000, "pid": os.getpid()}
                r_t = threading.Thread(target=resource_observer_thread, args=(args,))
                check_resource_threadId_set.add(r_t.ident)
                r_t.start()

                # ブラウザからHTML文などの情報取得
                browser_result = set_html(page=page, driver=driver)
                if "falsification.cysec.cs" in host:
                    logger.info("result of getting html by browser: %s, %s", page.url, browser_result)
                if type(browser_result) == list:     # 接続エラーの場合はlistが返る
                    logger.info("Failed to connect... Remaking headless browser")
                    browser_result = cast(List[str], browser_result)
                    update_write_file_dict('host', browser_result[0] + '.txt', content=browser_result[1])
                    # headless browser終了して作りなおしておく。
                    quit_driver(driver)
                    driver_info = get_fox_driver(queue_log, screenshots, user_agent=user_agent, org_path=org_path)
                    if driver_info is False:
                        error_break = True
                        r_t.run = False
                        r_t.join()
                        break
                    else:
                        driver_info = cast(Dict[str, Any], driver_info)
                        driver: WebDriver = driver_info["driver"]
                        watcher_window: Union[str, int] = driver_info["watcher_window"]
                        wait: WebDriverWait = driver_info["wait"]
                    # 次のURLへ
                    r_t.run = False
                    r_t.join()
                    continue

                # watchingを停止して、page.watcher_htmlにwatcher.htmlのデータを保存
                re = stop_watcher_and_get_data(driver=driver, wait=wait, watcher_window=watcher_window, page=page)
                if re is False:
                    logger.info("stop_watcher_and_get_data, break")
                    error_break = True
                    r_t.run = False
                    r_t.join()
                    break

                # watcher.htmlのHLTML文から、拡張機能によって取得した情報を抽出する
                # parserスレッドでしない理由は、リダイレクトが行われていると、parserスレッドを起動しないから
                extract_extension_data_and_inspection(page=page, filtering_dict=filtering_dict)

                # alertが出されていると、そのテキストを記録
                if page.alert_txt:
                    with wfta_lock:
                        write_file_to_alertdir.append(Alert(
                            url       = page.url_initial,
                            file_name = 'alert_text.csv',
                            content   = page.url_initial + ", " + page.url + ", " + str(page.alert_txt)[1:-1],
                            label     = 'InitialURL,URL,AlertText'
                        ))

                # about:blankなら以降の処理はしない
                if page.url == "about:blank":
                    with wfta_lock:
                        write_file_to_alertdir.append(Alert(
                            url       = page.url_initial,
                            file_name = 'about_blank_url.csv',
                            content   = page.url_initial + ', ' + page.src,
                            label     = 'InitialURL, src',
                        ))
                    r_t.run = False
                    r_t.join()
                    continue

                # リダイレクトのチェック
                redirect = check_redirect(page, host)
                if redirect is True:    # リダイレクトでサーバが変わっていれば
                    page_url_set = set(page.url)
                    result_set = inspection_url_by_filter(url_list=page_url_set, filtering_dict=filtering_dict)
                    send_to_parent(q_send, {'type': 'redirect', 'url_set': result_set, "ini_url": page.url_initial,
                                            "url_src": page.src})
                    r_t.run = False
                    r_t.join()
                    continue
                if redirect == "same":   # URLは変わったがサーバは変わらなかった場合は、処理の続行を親プロセスに通知
                    send_to_parent(sendq=q_send, data=(page.url, "redirect"))

                # ブラウザでurlが変わっている可能性があるため再度チェック
                if page.url in url_cache:
                    r_t.run = False
                    r_t.join()
                    continue

                # スクショが欲しければ撮る
                if screenshots:
                    if browser_result is True:
                        scsho_path = org_path + '/RAD/screenshots/' + dir_name
                        take_screenshots(scsho_path, driver)

                # 別窓やタブが開いた場合、そのURLを取得
                try:
                    window_url_list = get_window_url(driver, watcher_id=watcher_window, base_id=blank_window)
                except Exception as e1:
                    update_write_file_dict('result', 'window_url_get_error.txt',
                                           content=location() + '\n' + page.url + '\n' + str(e1))
                else:
                    if window_url_list:   # URLがあった場合、リンクURLを渡すときと同じ形にして親プロセスに送信
                        result_set = inspection_url_by_filter(url_list=window_url_list, filtering_dict=filtering_dict)
                        send_to_parent(q_send, {'type': 'new_window_url', 'url_set': result_set, "url_src": page.url})

                r_t.run = False
                r_t.join()

            logger.debug("%s: Parse start...", page.url)
            # スレッドを作成してパース開始(ブラウザで開いたページのHTMLソースをスクレイピングする)
            parser_thread_args_dic = {'host': host, 'page': page, 'q_send': q_send, 'file_type': file_type,
                                      'use_mecab': use_mecab, 'nth': nth, "filtering_dict": filtering_dict}
            t = threading.Thread(target=parser, args=(parser_thread_args_dic,))
            t.start()
            if type(t.ident) != None:
                ident = cast(int, t.ident)
                with parser_thread_lock:
                    parser_threadId_set.add(ident)  # スレッド集合に追加
                    parser_threads[ident] = {'thread': t, 'time':int(time())}  # スレッド開始時刻保存
            else:
                logger.critical("Unrechable bug, Failed to start thread")

            # ページの達成数をインクリメント
            num_of_pages += 1
        else:    # ウェブページではないファイルだった場合(PDF,excel,word...
            send_to_parent(q_send, {'type': 'file_done'})   # mainプロセスにこのURLのクローリング完了を知らせる
            if page.content_type == None:
                page.content_type = "None"
            # ハッシュ値の比較
            if url_dict:
                num_of_days, file_len = url_dict.compere_hash(page)
                if type(num_of_days) == int:
                    update_write_file_dict('result', 'change_hash_file.csv',
                                           content=['URL, content-type, no-change days', page.url + ', ' + page.content_type +
                                                    ', ' + str(num_of_days)])
                    if file_len is None:  # Noneは前回のファイルサイズが登録されていなかった場合
                        pass
                    else:  # ファイルサイズが変わっていたものを記録
                        update_write_file_dict('result', 'different_size_file.csv',
                                               content=['URL, src, content-type, difference, content-length',
                                                        page.url + ', ' + page.src + ', ' + page.content_type + ',' +
                                                        str(file_len) + ', ' + str(page.content_length)])
                elif num_of_days is True:     # ハッシュ値が同じ場合
                    update_write_file_dict('result', 'same_hash_file.csv',
                                           content=['URL, content-type', page.url + ', ' + page.content_type])
                elif num_of_days is False:  # 新規保存
                    update_write_file_dict('result', 'new_file.csv',
                                           content=['URL, content-type, src',
                                                    page.url + ', ' + page.content_type + ', ' + page.src])
            else:
                logger.error("there are no url_dict, unrechable Bug")
            # clamdによる検査
            if clamd_q is not False:  # Falseの場合はclamdを使わない
                clamd_q.put([page.url, page.src, page.html])

            # ファイルの達成数をインクリメント
            num_of_files += 1

        # 同じサーバばかり回り続けないように
        if not (num_of_pages+num_of_files % 100):  # 100URLをクローリングごとに保存して終了
            logger.info('%s: achievement have reached %d', host, num_of_pages + num_of_files)
            while parser_threadId_set:
                logger.debug('wait 3s for thread end....')
                sleep(3)
            break

        # 同じサーバばかり回り続けないように時間で切る
        if time() - start_time > LIMIT_TIME:
            logger.info('%s: spent over %d seconds, reached %d urls', host, LIMIT_TIME, num_of_pages + num_of_files)
            while parser_threadId_set:
                logger.debug('wait 3s for thread end....')
                sleep(3)
            break

    # error_break=Trueはブラウザ関連のエラーによりbreak
    if error_break:
        #  resource_ter_flag=Trueは資源監視スレッドによるブラウザ強制終了
        if resource_terminate_flag:
            logger.info("%s: Browser is killed", host)
            if page is not None:
                url_cache.add(page.url_initial)  # 親から送られてきたURL
                url_cache.add(page.url_urlopen)  # urlopenで得たURL
                url_cache.add(page.url)  # 最終的にパースしたURL
        else:
            logger.warning("%s: Browser error occured", host)
    else:
        if page is not None:
            url_cache.add(page.url_initial)  # 親から送られてきたURL
            url_cache.add(page.url_urlopen)  # urlopenで得たURL
            url_cache.add(page.url)          # 最終的にパースしたURL

    save_result(alert_process_q)
    logger.info("%s %s: saved", datetime.now().strftime('%Y/%m/%d, %H:%M:%S'), host)
    if driver:
        quit_driver(driver) # headless browser終了して
    os._exit(0) # type: ignore
