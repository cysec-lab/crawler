from file_rw import w_file, r_file, wa_file
from webpage import Page
from urldict import UrlDict
from inspection_page import iframe_inspection, meta_refresh_inspection, get_meta_refresh_url, script_inspection
from inspection_page import title_inspection, invisible
from inspection_file import check_content_type
from use_web_driver import driver_get, set_html, set_request_url, get_window_url, take_screenshots, quit_driver
import os
from time import sleep, time
from copy import deepcopy
import pickle
import json
import threading
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from mecab import get_tf_dict_by_mecab, add_word_dic, make_tfidf_dict, get_top10_tfidf
from use_mysql import execute_query, get_id_from_url, register_url

html_special_char = list()       # URLの特殊文字を置換するためのリスト
threadId_set = set()         # パーサーのスレッドid集合
threadId_time = dict()       # スレッドid : 実行時間
dir_name = ''                # このプロセスの作業ディレクトリ
f_name = ''                  # このプロセスのホスト名をファイル名として使えるように変換したもの
# semaphore = threading.Semaphore(3)     # ダウンロードチェックするためのスレッド数を制限
word_idf_dict = dict()                 # 前回にこのサーバに出てきた単語とそのidf値
word_df_dict = dict()                  # 今回、このサーバに出てきた単語と出現ページ数
word_df_lock = threading.Lock()        # word_df_dict更新の際のlock
num_of_achievement = 0       # 実際に取得してパースしたファイルやページの数。ジャンプ前URL、エラーだったURLは含まない。
url_cache = set()            # 接続を試したURLの集合。他サーバへのリダイレクトURLも入る。プロセスが終わっても消さずに保存する。
urlDict = None              # サーバ毎のurl_dictの辞書を扱うクラス
request_url_host_set = set()       # 各ページを構成するためにGETしたurlのネットワーク名の集合
request_url_host_set_pre = set()   # 今までのクローリング時のやつ
iframe_src_set = set()      # iframeのsrc先urlの集合
iframe_src_set_pre = set()  # 今までのクローリング時のやつ
iframe_src_set_lock = threading.Lock()   # これは更新をcrawlerスレッド内で行うため排他制御しておく
script_src_set = set()      # scriptのsrc先urlの集合
script_src_set_pre = set()  # 今までのクローリング時のやつ
script_src_set_lock = threading.Lock()   # これは更新をcrawlerスレッド内で行うため排他制御しておく
link_set = set()      # ページに貼られていたリンク先URLのネットワーク名の集合
link_set_pre = set()  # 今までのクローリング時のやつ
link_set_lock = threading.Lock()  # これは更新をcrawlerスレッド内で行うため排他制御しておく
frequent_word_list = list()   # 今までこのサーバに出てきた頻出単語top50

write_file_to_hostdir = dict()    # server/www.ac.jp/の中に作るファイルの内容。{file名 : [文字, 内容, ...], file名 : []}
wfth_lock = threading.Lock()      # write_file_to_hostdir更新の際のlock
write_file_to_resultdir = dict()  # result/result_*/の中に作るファイルの内容。{file名 : [内容, 内容, ...], file名 : []}
wftr_lock = threading.Lock()      # write_file_to_maindir更新の際のlock
write_file_to_alertdir = list()   # result/alert/の中に作るファイルの内容。辞書のリスト
wfta_lock = threading.Lock()      # write_file_to_alertdir更新の際のlock


def init(host, screenshots):
    global html_special_char, script_src_set, script_src_set_pre
    global num_of_achievement, dir_name, f_name, word_idf_dict, word_df_dict, url_cache, urlDict, frequent_word_list
    global request_url_host_set, request_url_host_set_pre, iframe_src_set, iframe_src_set_pre, link_set, link_set_pre
    data_temp = r_file('../../ROD/LIST/HTML_SPECHAR.txt')
    data_temp = data_temp.split('\n')
    for line in data_temp:
        line = line.split('\t')
        html_special_char.append(tuple(line))
    html_special_char.append(('\r', ''))
    html_special_char.append(('\n', ''))
    if not os.path.exists('server'):
        try:
            os.mkdir('server')
        except FileExistsError:
            pass
    dir_name = host.replace(':', '-')
    f_name = dir_name.replace('.', '-')
    if not os.path.exists('server/' + dir_name):
        try:
            os.mkdir('server/' + dir_name)
        except FileExistsError:
            pass
    if screenshots:
        if not os.path.exists('../../RAD/screenshots/' + dir_name):
            try:
                os.mkdir('../../RAD/screenshots/' + dir_name)
            except FileExistsError:
                pass
    os.chdir('server/' + dir_name)

    # 途中保存をロード
    if os.path.exists('../../../../RAD/temp/progress_' + f_name + '.pickle'):
        with open('../../../../RAD/temp/progress_' + f_name + '.pickle', 'rb') as f:
            data_temp = pickle.load(f)
            num_of_achievement = data_temp['num']
            url_cache = deepcopy(data_temp['cache'])
            request_url_host_set = deepcopy(data_temp['request'])
            iframe_src_set = deepcopy(data_temp['iframe'])
            script_src_set = deepcopy(data_temp['script'])
            if 'link_host' in data_temp:
                link_set = deepcopy(data_temp['link_host'])
    # 今までのクローリングで集めた、この組織の全request_url(のネットワーク部)をロード
    path = '../../../../ROD/request_url/matome.json'
    if os.path.exists(path):
        with open(path, 'r') as f:
            data_temp = json.load(f)
            request_url_host_set_pre = set(data_temp)
    # 今までのクローリングで集めた、この組織の全iframeタグのsrc値をロード
    path = '../../../../ROD/iframe_url/matome.json'
    if os.path.exists(path):
        with open(path, 'r') as f:
            data_temp = json.load(f)
            iframe_src_set_pre = set(data_temp)
    # 今までのクローリングで集めた、この組織の全scriptタグのsrc値をロード
    path = '../../../../ROD/script_url/matome.json'
    if os.path.exists(path):
        with open(path, 'r') as f:
            data_temp = json.load(f)
            script_src_set_pre = set(data_temp)
    # 今までのクローリングで集めた、この組織のリンクURL(のネットワーク部)をロード
    path = '../../../../ROD/link_url/matome.json'
    if os.path.exists(path):
        with open(path, 'r') as f:
            data_temp = json.load(f)
            link_set_pre = set(data_temp)
    # 今までのクローリングで集めた、このサーバの頻出単語をロード
    path = '../../../../ROD/frequent_word_100/' + f_name + '.json'
    if os.path.exists(path):
        with open(path, 'r') as f:
            data_temp = json.load(f)
            frequent_word_list = list(data_temp)
    # idf辞書をロード
    path = '../../../../ROD/idf_dict/' + f_name + '.json'
    if os.path.exists(path):
        if os.path.getsize(path) > 0:
            with open(path, 'r') as f:
                word_idf_dict = json.load(f)
    # df辞書をロード
    path = '../../../../RAD/df_dict/' + f_name + '.pickle'
    if os.path.exists(path):
        if os.path.getsize(path) > 0:
            with open(path, 'rb') as f:
                word_df_dict = pickle.load(f)
    urlDict = UrlDict(f_name)
    copy_flag = urlDict.load_url_dict(path=None)
    if copy_flag:
        wa_file('../../notice.txt', host + ' : copy' + copy_flag + ' because JSON data is broken.\n')


# クローリングして得たページの情報を外部ファイルに記録
def save_result(alert_process_q):
    urlDict.save_url_dict()
    if word_df_dict:
        path = '../../../../RAD/df_dict/' + f_name + '.pickle'
        with open(path, 'wb') as f:
            pickle.dump(word_df_dict, f)
    if num_of_achievement:
        with open('../../../../RAD/temp/progress_' + f_name + '.pickle', 'wb') as f:
            pickle.dump({'num': num_of_achievement, 'cache': url_cache, 'request': request_url_host_set,
                         'iframe': iframe_src_set, 'link_host': link_set, 'script': script_src_set}, f)
    w_file('achievement.txt', str(num_of_achievement))
    for file_name, value in write_file_to_hostdir.items():
        text = ''
        for i in value:
            if type(i) == list:
                if not os.path.exists(file_name):
                    text += i[0] + '\n'
                text += i[1] + '\n'
            else:
                text += i + '\n'
        wa_file(file_name, text)
    for file_name, value in write_file_to_resultdir.items():
        text = ''
        for i in value:
            if type(i) == list:
                if not os.path.exists('../../' + file_name):
                    text += i[0] + '\n'
                text += i[1] + '\n'
            else:
                text += i + '\n'
        # 偽サイトの結果ファイルはresultディレに書かない
        if 'falsification.cysec.cs.ritsumei.ac.jp' in dir_name:
            wa_file(file_name, text)
        else:
            wa_file('../../' + file_name, text)
    for data_dict in write_file_to_alertdir:
        alert_process_q.put(data_dict)
        # text = ''
        # for i in value:
        #     if type(i) == list:
        #         if not os.path.exists('../../../alert/' + file_name):
        #             text += i[0] + '\n'
        #         text += i[1] + '\n'
        #     else:
        #         text += i + '\n'
        # # 偽サイトの結果ファイルはalertディレに書かない
        # if 'falsification.cysec.cs.ritsumei.ac.jp' in dir_name:
        #     wa_file(file_name, text)
        # else:
        #     wa_file('../../../alert/' + file_name, text)


# クローリングの結果を外部ファイルに出力したいが、毎度していてはディスク書き込みが頻発するため
# 変数に内容を保存して置き、このプロセスが終わる時に一気に書き込む。そのための変数に保存をする関数。
def update_write_file_dict(dic_type, key, content):
    lock = None   # マルチスレッドの中から呼び出されることもあるため、排他制御をしておく
    dic = None
    # どのフォルダに保存するファイルか選択
    if dic_type == 'host':
        dic = write_file_to_hostdir
        lock = wfth_lock
    elif dic_type == 'result':
        dic = write_file_to_resultdir
        lock = wftr_lock
    elif dic_type == 'alert':
        return 0
        # dic = write_file_to_alertdir
        # lock = wfta_lock
    # 各辞書は、ファイル名：[内容, 内容, ...]になるように
    # alertディレだけ、ファイル名：[辞書, 辞書, ...]  (summarize_alertプロセスに渡すため)
    with lock:
        if key.endswith('.csv'):         # csvファイルの場合、contentはリストで[ヘッダ, 内容]となっている
            if key not in dic:
                dic[key] = [content]     # csvファイルの一行目はヘッダも入れる
            else:
                dic[key].append(content[1])   # 1行目以降は、内容だけ入れる
        else:   # textファイルの場合
            if key not in dic:
                dic[key] = [content]
            else:
                dic[key].append(content)


# 親プロセスにdataを送信する
def send_to_parent(sendq, data):
    if not sendq.full():
        sendq.put(data)  # 親にdataを送信
    else:
        sleep(1)
        sendq.put(data)


# 親プロセスに送信する用のリンクを作成
def make_send_links_data(page):
    url_tuple_list = list()
    links = deepcopy(page.normalized_links)
    while links:
        link_url = links.pop()
        url_tuple_list.append((link_url, page.url))  # [(link_url, url),(link_url, url),..,()]になる
    return {'type': 'links', 'url_tuple_list': url_tuple_list}


# HTMLソースからリンク集を作る
def make_link(page, soup, page_type):
    # xml、htmlに分けてリンクを取り出し
    if page_type == 'xml':
        page.make_links_xml(soup)
    elif page_type == 'html':
        page.make_links_html(soup)
    # pageのリンク集のURLを補完する
    page.complete_links(html_special_char)


# iframeタグをさらに枠が設定されているかどうかで分けたタグのリスト
def special_course(tags):
    tag_list = list()
    for tag in tags:
        if tag.name == 'iframe':
            re = invisible([tag])    # 枠が0のiframeタグを探すときに使っている関数を借りる
            if re:   # width、heightのどちらかが0だった、もしくはwidth、height属性値が設定されていなかった場合
                tag_list.append('invisible_iframe')
            else:
                tag_list.append('iframe')   # width、heightに0以外が設定されていた
        else:
            tag_list.append(tag.name)
    return tag_list


def get_tags_from_html(soup, page, machine_learning_q):
    # 正確にタグ情報を取得するためにprettifyで整形したソースコードからもう一度soupを作る
    try:
        soup2 = BeautifulSoup(soup.prettify(), 'lxml')
    except Exception:
        soup2 = BeautifulSoup(soup.prettify(), 'html.parser')

    # 全てのtagを取り出し、MLプロセスへ送信
    tags = soup2.find_all()
    tag_list = [tag.name for tag in tags]   # tagの名前だけ取り出す
    if tag_list:
        if 'iframe' in tag_list:   # iframeがあれは
            tag_list = special_course(tags)   # ちょっといじる

        urlDict.add_tag_data(page, tag_list)   # 外部ファイルへ保存するためのクラスへ格納
        if machine_learning_q is not False:
            # 機械学習プロセスへ送信
            dic = {'url': page.url, 'src': page.src, 'tags': tag_list, 'host': f_name}
            machine_learning_q.put(dic)


def make_query(mysql, url, table_type, contents):
    conn = mysql['conn']
    n = mysql['n']
    query_list = list()
    value_list = list()
    tables = table_type + '_url_' + n

    # urlからidを取得する
    url_id = get_id_from_url(conn, url, n)
    if url_id is None:
        register_url(conn, url, n)
    elif url_id is False:
        return query_list, value_list

    for string in contents:
        query = 'INSERT INTO ' + tables + ' (url_id, ' + table_type + ') VALUES (%s, %s)'
        query_list.append(query)
        value = [str(url_id), string]
        value.append(value)

    return query_list, value_list


def parser(parse_args_dic):
    global word_df_dict
    host = parse_args_dic['host']
    page = parse_args_dic['page']
    q_send = parse_args_dic['q_send']
    file_type = parse_args_dic['file_type']
    machine_learning_q = parse_args_dic['machine_learning_q']
    use_mecab = parse_args_dic['use_mecab']
    mysql = parse_args_dic['mysql']
    screenshots_svc_q = parse_args_dic['screenshots_svc_q']
    img_name = parse_args_dic['img_name']
    nth = parse_args_dic['nth']

    # スクレイピングするためのsoup
    try:
        soup = BeautifulSoup(page.html, 'lxml')
    except Exception:
        soup = BeautifulSoup(page.html, 'html.parser')

    # htmlソースからtagだけ取り出して機械学習に入れる
    get_tags_from_html(soup, page, machine_learning_q)

    # ページに貼られているリンク集を作り、親プロセスへ送信
    make_link(page, soup, page_type=file_type)  # ページに貼られているリンクを取得
    send_data = make_send_links_data(page)      # 親に送るURLリストを作成
    send_to_parent(q_send, send_data)           # 親にURLリストを送信

    # リンク集をデータベースに保存
    if mysql is not False:
        query_list, value_list = make_query(mysql, url=page.url, table_type='link', contents=page.normalized_links)
        execute_query(conn=mysql['conn'], query_list=query_list, value_list=value_list)

    # 検査
    # 前回とのハッシュ値を比較
    num_of_days, file_len = urlDict.compere_hash(page)
    if type(num_of_days) == int:  # int型ならハッシュ値が違う。Trueは変化なし。Falseは新規ページ、Noneはエラー。
        update_write_file_dict('result', 'change_hash_page.csv',
                               content=['URL,num of no-change days', page.url + ',' + str(num_of_days)])
    elif num_of_days is True:
        update_write_file_dict('result', 'same_hash_page.csv', content=['URL', page.url])
    elif num_of_days is False:
        update_write_file_dict('result', 'new_page.csv', content=['URL,src', page.url + ',' + page.src])
        page.new_page = True

    if use_mecab:
        # このページの各単語のtf値を計算、df辞書を更新
        hack_level, word_tf_dict = get_tf_dict_by_mecab(soup)  # tf値の計算と"hacked by"検索
        if 'falsification' in host:
            wa_file('hacked.csv', page.url + ',' + str(hack_level) + '\n')
        if hack_level:    # hackの文字が入っていると0以外が返ってくる
            if hack_level == 1:
                update_write_file_dict('result', 'hack_word_Lv' + str(hack_level) + '.txt', content=page.url)
            else:
                data_temp = dict()
                data_temp['url'] = page.url
                data_temp['src'] = page.src
                data_temp['file_name'] = 'hack_word_Lv' + str(hack_level) + '.csv'
                data_temp['content'] = page.url + ',' + page.src
                data_temp['label'] = 'URL,SOURCE'
                with wfta_lock:
                    write_file_to_alertdir.append(data_temp)
        if word_tf_dict is not False:
            with word_df_lock:
                word_df_dict = add_word_dic(word_df_dict, word_tf_dict)  # サーバのidf計算のために単語と出現ページ数を更新
            if word_idf_dict:
                word_tfidf = make_tfidf_dict(idf_dict=word_idf_dict, tf_dict=word_tf_dict)  # tf-idf値を計算
                top10 = get_top10_tfidf(tfidf_dict=word_tfidf, nth=nth)   # top10を取得。ページ内に単語がなかった場合は空リストが返る
                # ハッシュ値が異なるため、重要単語を比較
                # if num_of_days is not True:
                if True:  # 実験のため毎回比較
                    pre_top10 = urlDict.get_top10_from_url_dict(url=page.url)    # 前回のtop10を取得
                    if pre_top10 is not None:
                        symmetric_difference = set(top10) ^ set(pre_top10)         # 排他的論理和
                        if len(symmetric_difference) > 16:
                            data_temp = dict()
                            data_temp['url'] = page.url
                            data_temp['src'] = page.src
                            data_temp['file_name'] = 'change_important_word.csv'
                            data_temp['content'] = page.url + ',' + str(top10) + ',' + str(pre_top10)
                            data_temp['label'] = 'URL,TOP10,PRE'
                            with wfta_lock:
                                write_file_to_alertdir.append(data_temp)
                            if screenshots_svc_q is not False:
                                data_dic = {'host': dir_name, 'url': page.url, 'img_name': img_name,
                                            'num_diff_word': len(symmetric_difference)}
                                screenshots_svc_q.put(data_dic)
                        update_write_file_dict('result', 'symmetric_diff_of_word.csv',
                                               content=['URL,length,top10,pre top10', page.url + ',' +
                                                        str(len(symmetric_difference)) + ',' + str(top10) + ',' +
                                                        str(pre_top10) + ',' + str(num_of_days)])
                urlDict.add_top10_to_url_dict(url=page.url, top10=top10)          # top10を更新

            # ページにあった単語が今までの頻出単語にどれだけ含まれているか調査-------------------------------
            if frequent_word_list:
                """
                n = 60
                # 上位n個と比較し、頻出単語に含まれていなかった単語の数を保存
                max_num = min(len(frequent_word_list), n)  # 保存されている単語数がn個未満のサーバがあるため
                and_ = set(word_tf_dict.keys()).intersection(set(frequent_word_list[0:max_num]))
                and_list = list()
                and_list.append(len(and_))
                while n < 100:
                    n += 10
                    max_num = min(len(frequent_word_list), n)  # 保存されている単語数がn個未満のサーバがあるため
                    and_ = set(word_tf_dict.keys()).intersection(set(frequent_word_list[0:max_num]))
                    and_list.append(len(and_))
                    if max_num == len(frequent_word_list):
                        break
                update_write_file_dict('result', 'frequent_word_investigation.csv',
                                       ['URL,new', page.url + ',' + str(page.new_page) + ',' +
                                        str(and_list)[1:-1].replace(' ', '')])
                """
                n = 50
                # 上位50個と比較し、頻出単語に含まれていなかった単語の数を保存
                # (frequent_word_listには、サイトの頻出単語が上位100個まで保存されているが、50個で十分と判断)
                max_num = min(len(frequent_word_list), n)  # 保存されている単語数がn個未満のサーバがあるため
                and_set = set(word_tf_dict.keys()).intersection(set(frequent_word_list[0:max_num]))

                # このページにある単語から頻出単語リストの単語を引き、その数を調べる
                diff_set = set(word_tf_dict.keys()).difference(set(frequent_word_list[0:max_num]))
                update_write_file_dict('result', 'and_diff_of_word_in_new_page.csv',
                                       ['URL,and,diff,per', page.url + ',' + str(len(and_set)) + ',' +
                                        str(len(diff_set)) + ',' + str(len(diff_set)/len(word_tf_dict.keys()))])

                # 新しく見つかったURLで、ANDの単語(このページの単語と今までの頻出単語top50とのAND)が5個以下なら
                if len(and_set) < 6 and page.new_page:
                    data_temp = dict()
                    data_temp['url'] = page.url
                    data_temp['src'] = page.src
                    data_temp['file_name'] = 'new_page_without_frequent_word.csv'
                    data_temp['content'] = page.url + ',' + str(and_set)
                    data_temp['label'] = 'URL,WORDS'
                    with wfta_lock:
                        write_file_to_alertdir.append(data_temp)

    # iframeの検査
    iframe_result = iframe_inspection(soup)     # iframeがなければFalse
    if iframe_result:
        if iframe_result['iframe_src_list']:    # iframeのsrcURLのリストがあれば
            with iframe_src_set_lock:   # 今回見つかったiframeのsrc集合の更新
                iframe_src_set.update(set(iframe_result['iframe_src_list']))
            if iframe_src_set_pre:   # 前回のクローリング時のiframeのsrcデータがあれば
                diff = set(iframe_result['iframe_src_list']).difference(iframe_src_set_pre)   # 差をとる
                if diff:   # 前回のクローリング時に確認されなかったサーバのiframeが使われているならば
                    content_str = ''
                    for i in diff:
                        content_str += ',' + i
                    data_temp = dict()
                    data_temp['url'] = page.url
                    data_temp['src'] = page.src
                    data_temp['file_name'] = 'new_iframeSrc.csv'
                    data_temp['content'] = page.url + content_str
                    data_temp['label'] = 'URL,iframe_src'
                    with wfta_lock:
                        write_file_to_alertdir.append(data_temp)
        # 目に見えないiframeがあるか。javascriptを動かすために結構見つかる。
        if iframe_result['invisible_iframe_list']:
            update_write_file_dict('result', 'invisible_iframe.csv', content=['URL', page.url])

    # meta Refreshの検査
    meta_refresh_result = meta_refresh_inspection(soup)    # http-equivがrefreshのタグのリスト取ってくる(なければFalse
    if meta_refresh_result:
        meta_refresh = ''
        for i in meta_refresh_result:
            meta_refresh += str(i) + ','
        update_write_file_dict('result', 'meta_refresh.csv', content=['URL,meta-ref', page.url + ',' + meta_refresh])
        send_list = get_meta_refresh_url(meta_refresh_result, page)   # refreshタグからURLを抽出
        # 親にURLを送信する。リダイレクトと同じ扱いをするため、複数あっても(そんなページ怪しすぎるが)１つずつ送る
        while send_list:
            send_to_parent(q_send, {'type': 'redirect', 'url_tuple_list': [send_list.pop()]})

    # scriptに関して
    # script名が特徴的かどうか。[(スクリプト名, そのスクリプトタグ),()...]となるリストを返す
    script_result = script_inspection(soup=soup)
    if script_result:
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
        # 前回のクローリングで見つかっていないscript名があるか
        if script_result['script_src_list']:    # iframeのsrcURLのリストがあれば
            with script_src_set_lock:   # 今回見つかったiframeのsrc集合の更新
                script_src_set.update(set(script_result['script_src_list']))
            if script_src_set_pre:   # 前回のクローリング時のiframeのsrcデータがあれば
                diff = set(script_result['script_src_list']).difference(script_src_set_pre)   # 差をとる
                if diff:   # 前回のクローリング時に確認されなかったサーバのURLがscriptに使われているならば
                    content_str = ''
                    for i in diff:
                        content_str += ',' + i
                    data_temp = dict()
                    data_temp['url'] = page.url
                    data_temp['src'] = page.src
                    data_temp['file_name'] = 'new_scriptSrc.csv'
                    data_temp['content'] = page.url + content_str
                    data_temp['label'] = 'URL,script_src'
                    with wfta_lock:
                        write_file_to_alertdir.append(data_temp)

    # requestURLで、同じサーバのもので前回にないものがあるか比較
    if page.request_url:
        diff = urlDict.compare_request_url(page)
        if diff:
            pass
            # update_write_file_dict('alert', 'in_same_server.csv', content=['URL,diff', page.url + ',' + str(diff)])
    # requestURL と requestURLで同じサーバのURL を url_dictに追加
    if page.request_url:
        urlDict.add_request_url_to_url_dict(page)

    # 貼られていたリンクの中に、このサーバのウェブページが今まで貼ったことのないサーバへのリンクがあるかチェック
    if page.normalized_links:
        url_domain_set_temp = set([urlparse(url).netloc for url in page.normalized_links])  # リンク集からホスト名だけの集合を作成
        url_domain_set = set()
        for url_domain in url_domain_set_temp:  # ホスト部がある場合は、ホスト部は削除し、ネットワーク名のみにする
            if url_domain.count('.') > 2:   # xx.ac.jpのように「.」が2つしかないものはそのまま
                url_domain = '.'.join(url_domain.split('.')[1:])   # www.ritsumei.ac.jpは、ritsumei.ac.jpにする
            url_domain_set.add(url_domain)
        with link_set_lock:  # リンク集合の更新
            link_set.update(url_domain_set)
        if link_set_pre:  # 前回のデータがあれば
            diff = url_domain_set.difference(link_set_pre)  # 差をとる
            if diff:  # 今まで確認されなかったサーバへのリンクが貼られていれば
                temp = list()
                for link_host in diff:   # ページのリンク集から、ホスト名に特定のネットワーク部を含むURLを取ってくる
                    temp.extend([url for url in page.normalized_links if link_host in urlparse(url).netloc])
                content_str = ''
                for i in temp:
                    if host == urlparse(i).netloc:  # 自分自身のサーバへのリンクURLの場合
                        continue
                    content_str += ',' + i
                if content_str:
                    data_temp = dict()
                    data_temp['url'] = page.url
                    data_temp['src'] = page.src
                    data_temp['file_name'] = 'link_to_new_server.csv'
                    data_temp['content'] = page.url + content_str
                    data_temp['label'] = 'URL,LINK'
                    with wfta_lock:
                        write_file_to_alertdir.append(data_temp)

    # スレッド集合から削除
    try:
        threadId_set.remove(threading.get_ident())   # del_thread()で消されていた場合、KeyErrorになる
        del threadId_time[threading.get_ident()]
    except KeyError as e:
        print(host + ' : ' + 'thread was deleted. : ' + page.url + ' : ' + str(e))


# 180秒以上続いているスレッドのリストを返す
def check_thread_time(now):
    thread_list = list()
    try:
        for threadId, th_time in threadId_time.items():
            if (now - th_time) > 180:
                thread_list.append(threadId)
    except RuntimeError as e:
        print(e)
    return thread_list


# 5秒間隔で180秒以上続いているスレッドがあるかチェックし、あるとリストから削除
def del_thread(host):
    while True:
        sleep(5)
        del_thread_list = check_thread_time(int(time()))
        for th in del_thread_list:
            print(host + ' del: ' + str(th))
            try:
                threadId_set.remove(th)   # 消去処理がパーススレッドとほぼ同時に行われるとなるかも？(多分ない)
                del threadId_time[th]
            except KeyError as e:
                print(host + ' : del_thread-function KeyError :' + str(e))


# 5秒間受信キューに何も入っていなければFalseを返す
# 送られてくるのは、(URL, src)　か　'nothing'
def receive(recv_r):
    try:
        temp_r = recv_r.get(block=True, timeout=5)
    except Exception as e:
        print(f_name + ' : ' + str(e), flush=True)
        return False
    return temp_r


# ウェブページなら文字列、そうでないならFalseを返す
def page_or_file(page):
    if page.content_type == '':
        return False
    elif 'plain/xml' in page.content_type:
        return 'xml'
    elif 'text/xml' in page.content_type:
        return 'xml'
    elif 'application/xml' in page.content_type:
        return 'xml'
    elif 'html' in page.content_type:
        return 'html'
    else:
        return False


# URLが変わっていなければFalse、リダイレクトしていても同じサーバ内ならば'same'、違うサーバならTrue
def check_redirect(page, host):
    if page.url_initial == page.url:
        return False
    if host == page.hostName:
        return 'same'
    return True


# 接続間隔はurlopen接続後、phantomJS接続後、それぞれ接続する関数内で１秒待機
def crawler_main(args_dic):
    global num_of_achievement, request_url_host_set

    # 引数取り出し
    host = args_dic['host_name']
    q_recv = args_dic['parent_sendq']
    q_send = args_dic['child_sendq']
    clamd_q = args_dic['clamd_q']
    screenshots = args_dic['screenshots']
    machine_learning_q = args_dic['machine_learning_q']
    screenshots_svc_q = args_dic['screenshots_svc_q']
    phantomjs = args_dic['phantomjs']
    use_mecab = args_dic['mecab']
    mysql = args_dic['mysql']
    alert_process_q = args_dic['alert_process_q']
    nth = args_dic['nth']

    # PhantomJSを使うdriverを取得、一つのプロセスは一つのPhantomJSを使う
    if phantomjs:
        driver = driver_get(screenshots)
        if driver is False:
            print(host + ' : cannot make PhantomJS process', flush=True)
            os._exit(0)

    page = None

    # 保存データのロードや初めての場合は必要なディレクトリの作成などを行う
    init(host, screenshots)

    # 180秒以上パースに時間がかかるスレッドは削除する(ためのスレッド)...実際にそんなスレッドがあるかは不明
    t = threading.Thread(target=del_thread, args=(host,))
    t.daemon = True
    t.start()

    # クローラプロセスメインループ
    while True:
        # 動いていることを確認
        # if page is None:
        #     print(host + ' : main loop is running...')
        # else:
        #     print(host + ' : ' + str(page.url_initial) + '  :  DONE')

        # 前回(一個前のループ)のURLを保存、driverはクッキー消去
        if page is not None:
            url_cache.add(page.url_initial)   # 親から送られてきたURL
            url_cache.add(page.url_urlopen)   # urlopenで得たURL
            url_cache.add(page.url)           # 最終的にパースしたURL
            page = None
        try:
            driver.delete_all_cookies()   # クッキー削除
        except Exception:
            pass

        # クローリングするURLを取得
        send_to_parent(sendq=q_send, data='plz')   # 親プロセスにURLを要求
        search_tuple = receive(q_recv)             # 5秒間何も届かなければFalse
        if search_tuple is False:
            #print(host + " : couldn't get data from main process.")
            while threadId_set:   # 実行中のパーススレッドがあるならば
                #print(host + ' : wait 3sec because the queue is empty.')
                sleep(3)
            break
        elif search_tuple == 'nothing':   # このプロセスに割り当てるURLがない場合は"nothing"を受信する
            #print(host + ' : nothing!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            while threadId_set:
                #print(host + ' : wait 3sec for finishing parse thread')
                sleep(3)
            # 3秒待機後、もう一度要求する
            sleep(3)
            send_to_parent(sendq=q_send, data='plz')   # plz要求
            search_tuple = receive(q_recv)             # 応答確認
            if type(search_tuple) is tuple:
                send_to_parent(q_send, 'receive')
            else:
                # ２回目もFalse or nothingだったらメインを抜ける
                break
        else:    # それ以外(URLのタプル)
            #print(host + ' : ' + search_tuple[0] + ' : RECEIVE')
            send_to_parent(q_send, 'receive')

        # 検索するURLを取得
        url, url_src = search_tuple  # 親から送られてくるURLは、(URL, リンク元URL)のタプル
        if url in url_cache:    # 既にクローリング済ならば次へ。
            continue           # ここに当てはまるのは、NOT FOUNDページとかリダイレクトされた後のURLとか？

        # Pageオブジェクトを作成
        page = Page(url, url_src)

        # urlopenで接続
        urlopen_result = page.set_html_and_content_type_urlopen(page.url, time_out=60)
        if type(urlopen_result) is list:  # listが返るとエラー
            # URLがこのサーバの中でひとつ目だった場合
            if num_of_achievement:
                update_write_file_dict('host', urlopen_result[0]+'.txt', content=urlopen_result[1])
                continue
            # ひとつ目のURLだった場合、もう一度やってみる
            update_write_file_dict('host', urlopen_result[0]+'.txt', content=urlopen_result[1] + ', and try again')
            urlopen_result = page.set_html_and_content_type_urlopen(page.url, time_out=90)  # 次は90秒待機する
            if type(urlopen_result) is list:  # それでも無理なら諦める
                update_write_file_dict('host', urlopen_result[0] + '.txt', content=urlopen_result[1])
                continue
        # リダイレクトのチェック
        redirect = check_redirect(page, host)
        if redirect is True:   # 別サーバへリダイレクトしていればTrue
            send_to_parent(q_send, {'type': 'redirect', 'url_tuple_list': [(page.url, page.src, page.url_initial)]})
            continue
        if redirect == "same":    # 同じホスト内のリダイレクトの場合、処理の続行を親プロセスに通知
            send_to_parent(sendq=q_send, data=(page.url, "redirect"))

        # urlopenでurlが変わっている可能性があるため再度チェック
        if page.url in url_cache:
            continue

        # content-typeからウェブページ(str)かその他ファイル(False)かを判断
        file_type = page_or_file(page)
        update_write_file_dict('host', 'content-type.csv', ['content-type,url,src', page.content_type.replace(',', ':')
                                                            + ',' + page.url + ',' + page.src])  # 記録

        if type(file_type) is str:   # ウェブページの場合
            img_name = False
            if phantomjs:
                # phantomJSでURLに再接続。関数内で接続後１秒待機
                phantom_result = set_html(page=page, driver=driver)
                if type(phantom_result) == list:     # 接続エラーの場合はlistが返る
                    update_write_file_dict('host', phantom_result[0] + '.txt', content=phantom_result[1])
                    quit_driver(driver)    # headless browser終了して
                    driver = driver_get(screenshots)  # 再取得
                    if driver is False:
                        os._exit(0)
                    else:
                        phantom_result = set_html(page=page, driver=driver)   # もっかい接続を試してみる
                        if type(phantom_result) == list:                # ２回目もエラーなら次のURLへ(諦める)
                            continue
                # about:blankなら以降の処理はしない
                if page.url == "about:blank":
                    data_temp = dict()
                    data_temp['url'] = page.url_initial
                    data_temp['src'] = page.src
                    data_temp['file_name'] = 'about_blank_url.csv'
                    data_temp['content'] = page.url_initial + ',' + page.src
                    data_temp['label'] = 'URL,src'
                    with wfta_lock:
                        write_file_to_alertdir.append(data_temp)
                    with open('blank_file_' + str(num_of_achievement) + '.html_b', mode='wb') as f:
                        f.write(page.html_urlopen)
                    continue

                # リダイレクトのチェック
                redirect = check_redirect(page, host)
                if redirect is True:    # リダイレクトでサーバが変わっていれば
                    send_to_parent(q_send, {'type': 'redirect',
                                            'url_tuple_list': [(page.url, page.src, page.url_initial)]})
                    continue
                if redirect == "same":   # URLは変わったがサーバは変わらなかった場合は、処理の続行を親プロセスに通知
                    send_to_parent(sendq=q_send, data=(page.url, "redirect"))

                # phantomJSでurlが変わっている可能性があるため再度チェック
                if page.url in url_cache:
                    continue
                """
                # javascript実行し、PhantomJSで自動ダウンロードチェック
                t = threading.Thread(target=download_check, args=(page.url_urlopen, page.url, host,),)
                t.start()
                threadId_set.add(t.ident)  # スレッド集合に追加
                threadId_time[t.ident] = int(time())
                # aタグで、href属性がなく、onclick属性があるものをクリックし、URLのジャンプを確認
                click_a_tags(driver=driver, q_send=q_send, url_ini=page.url)
                """

                # ページをロードする際にリクエストしたURLをpageオブジェ内に保存
                try:
                    test = set_request_url(page, driver)    # testにはGET、POSTメソッド以外のメソッドがあれば入る
                except Exception:
                    test = False
                if page.request_url:
                    request_url_host_set = request_url_host_set.union(set(page.request_url_host))
                    if request_url_host_set_pre:
                        diff = set(page.request_url_host).difference(request_url_host_set_pre)
                        if diff:
                            str_t = ''
                            for t in diff:
                                if t in host:   # 自分自身のサーバへのリクエストURLの場合
                                    continue
                                str_t += ',' + t
                            if str_t != '':
                                data_temp = dict()
                                data_temp['url'] = page.url
                                data_temp['src'] = page.src
                                data_temp['file_name'] = 'new_request_url.csv'
                                data_temp['content'] = page.url + str_t
                                data_temp['label'] = 'URL,request_url'
                                with wfta_lock:
                                    write_file_to_alertdir.append(data_temp)
                if test:
                    wa_file('../../method_except_forGETPOST.csv', page.url + ',' + page.src + ',' + str(test) + '\n')

                # スクショが欲しければ撮る
                if screenshots:
                    if phantom_result is True:
                        scsho_path = '../../../../RAD/screenshots/' + dir_name
                        take_screenshots(scsho_path, driver)

                # 別窓やタブが開いた場合、そのURLを取得
                try:
                    window_url_list = get_window_url(driver)
                except Exception as e:
                    wa_file('../../window_url_get_error.txt', data=page.url + '\n' + str(e) + '\n')
                else:
                    if window_url_list:   # URLがあった場合、リンクURLを渡すときと同じ形にして親プロセスに送信
                        url_tuple_list = list()
                        for url_temp in window_url_list:
                            url_tuple_list.append((url_temp, page.url))   # 作成タプルはリンクリストを作る時と同じ(URL, src)
                        send_to_parent(q_send, {'type': 'new_window_url', 'url_tuple_list': url_tuple_list})

            # スレッドを作成してパース開始(phantomJSで開いたページのHTMLソースをスクレイピングする)
            parser_thread_args_dic = {'host': host, 'page': page, 'q_send': q_send, 'file_type': file_type,
                                      'machine_learning_q': machine_learning_q, 'use_mecab': use_mecab, 'nth': nth,
                                      'mysql': mysql, 'screenshots_svc_q': screenshots_svc_q, 'img_name': img_name}
            t = threading.Thread(target=parser, args=(parser_thread_args_dic,))
            t.start()
            threadId_set.add(t.ident)  # スレッド集合に追加
            threadId_time[t.ident] = int(time())  # スレッド開始時刻保存
        else:    # ウェブページではないファイルだった場合(PDF,excel,word...
            send_to_parent(q_send, {'type': 'file_done'})   # mainプロセスにこのURLのクローリング完了を知らせる
            # ハッシュ値の比較
            num_of_days, file_len = urlDict.compere_hash(page)
            if type(num_of_days) == int:
                update_write_file_dict('result', 'change_hash_file.csv',
                                       content=['URL,content-type,no-change days', page.url + ',' + page.content_type +
                                                ',' + str(num_of_days)])
                if file_len is None:  # Noneは前回のファイルサイズが登録されていなかった場合
                    pass
                else:  # ファイルサイズが変わっていたものを記録
                    update_write_file_dict('result', 'different_size_file.csv',
                                           content=['URL,src,content-type,difference,content-length',
                                                    page.url + ',' + page.src + ',' + page.content_type + ',' +
                                                    str(file_len) + ',' + str(page.content_length)])
            elif num_of_days is True:     # ハッシュ値が同じ場合
                update_write_file_dict('result', 'same_hash_file.csv',
                                       content=['URL,content-type', page.url + ',' + page.content_type])
            elif num_of_days is False:  # 新規保存
                update_write_file_dict('result', 'new_file.csv',
                                       content=['URL,content-type,src',
                                                page.url + ',' + page.content_type + ',' + page.src])
            # clamdによる検査
            if clamd_q is not False:  # Falseの場合はclamdを使わない
                clamd_q.put([page.url, page.src, page.html])

        # 検索結果数をインクリメント
        num_of_achievement += 1
        if not (num_of_achievement % 100):  # 100URLをクローリングごとに保存して終了
            print(host + ' : achievement have reached ' + str(num_of_achievement))
            while threadId_set:
                print(host + ' : wait 3sec for thread end.')
                sleep(3)
            break

    if page is not None:
        url_cache.add(page.url_initial)  # 親から送られてきたURL
        url_cache.add(page.url_urlopen)  # urlopenで得たURL
        url_cache.add(page.url)          # 最終的にパースしたURL

    # q_send.put('save')
    save_result(alert_process_q)
    # q_send.put('done_save')
    print(host + ' saved.')
    quit_driver(driver)  # headless browser終了して
    os._exit(0)
