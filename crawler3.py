from file_rw import w_file, r_file, wa_file
from webpage import Page
from urldict import UrlDict
from inspection_page import iframe_inspection, meta_refresh_inspection, get_meta_refresh_url, script_inspection
from inspection_page import title_inspection, invisible
from inspection_file import check_content_type
from use_web_driver import driver_get, set_html, set_request_url, get_window_url
import os
from time import sleep, time
from copy import deepcopy
import pickle
import json
import threading
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from mecab import get_tf_dict_by_mecab, add_word_dic, make_tfidf_dict, get_top10_tfidf

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
request_url_host_set = set()       # 各ページを構成するためにGETしたurlのホスト名の集合
request_url_host_set_pre = set()   # 今までのクローリング時のやつ
iframe_src_set = set()      # iframeのsrc先urlのホスト名の集合
iframe_src_set_pre = set()  # 今までのクローリング時のやつ
iframe_src_set_lock = threading.Lock()   # これは更新をcrawlerスレッド内で行うため排他制御しておく
link_set = set()      # ページに貼られていたリンク先URLのホスト名の集合
link_set_pre = set()  # 今までのクローリング時のやつ
link_set_lock = threading.Lock()  # これは更新をcrawlerスレッド内で行うため排他制御しておく
frequent_word_list = list()   # 今までこのサーバに出てきた頻出単語top50

write_file_to_hostdir = dict()    # server/www.ac.jp/の中に作るファイルの内容。{file名 : [文字, 内容, ...], file名 : []}
wfth_lock = threading.Lock()      # write_file_to_hostdir更新の際のlock
write_file_to_resultdir = dict()  # result/result_*/の中に作るファイルの内容。{file名 : [内容, 内容, ...], file名 : []}
wftr_lock = threading.Lock()      # write_file_to_maindir更新の際のlock
write_file_to_alertdir = dict()   # result/alert/の中に作るファイルの内容。{file名 : [内容, 内容, ...], file名 : []}
wfta_lock = threading.Lock()      # write_file_to_alertdir更新の際のlock


def init(host, screenshots):
    global html_special_char
    global num_of_achievement, dir_name, f_name, word_idf_dict, word_df_dict, url_cache, urlDict, frequent_word_list
    global request_url_host_set, request_url_host_set_pre, iframe_src_set, iframe_src_set_pre, link_set, link_set_pre
    data_temp = r_file('../../ROD/LIST/HTML_SPECHAR.txt')
    data_temp = data_temp.split('\n')
    for line in data_temp:
        line = line.split('\t')
        html_special_char.append(tuple(line))
    html_special_char.append(('\r', ''))
    html_special_char.append(('\n', ''))
    try:
        os.mkdir('server')
    except FileExistsError:
        pass
    dir_name = host.replace(':', '-')
    f_name = dir_name.replace('.', '-')
    if not os.path.exists('server/' + dir_name):
        os.mkdir('server/' + dir_name)
    if screenshots:
        if not os.path.exists('../../image/' + dir_name):
            os.mkdir('../../image/' + dir_name)

    os.chdir('server/' + dir_name)

    # 途中保存をロード
    if os.path.exists('../../../../RAD/temp/progress_' + f_name + '.pickle'):
        with open('../../../../RAD/temp/progress_' + f_name + '.pickle', 'rb') as f:
            data_temp = pickle.load(f)
            num_of_achievement = data_temp['num']
            url_cache = deepcopy(data_temp['cache'])
            request_url_host_set = deepcopy(data_temp['request'])
            iframe_src_set = deepcopy(data_temp['iframe'])
            if 'link_host' in data_temp:
                link_set = deepcopy(data_temp['link_host'])
    # 今までのクローリングで集めた、このサーバの全request_url(のホスト部)をロード
    path = '../../../../ROD/request_url/' + f_name + '.json'
    if os.path.exists(path):
        with open(path, 'r') as f:
            data_temp = json.load(f)
            request_url_host_set_pre = set(data_temp)
    # 今までのクローリングで集めた、このサーバの全iframeタグのsrc属性(のホスト部)をロード
    path = '../../../../ROD/iframe_src/' + f_name + '.json'
    if os.path.exists(path):
        with open(path, 'r') as f:
            data_temp = json.load(f)
            iframe_src_set_pre = set(data_temp)
    # 今までのクローリングで集めた、このサーバのリンクURL(のホスト部)をロード
    path = '../../../../ROD/link_host/' + f_name + '.json'
    if os.path.exists(path):
        with open(path, 'r') as f:
            data_temp = json.load(f)
            link_set_pre = set(data_temp)
    # 今までのクローリングで集めた、このサーバの頻出単語をロード
    path = '../../../../ROD/frequent_word_50/' + f_name + '.json'
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
    path = '../../../../RAD/df_dict/' + f_name + '.json'
    if os.path.exists(path):
        if os.path.getsize(path) > 0:
            with open(path, 'r') as f:
                word_df_dict = json.load(f)
    urlDict = UrlDict(f_name)


# クローリングして得たページの情報を外部ファイルに記録
def save_result():
    urlDict.save_url_dict()
    if word_df_dict:
        path = '../../../../RAD/df_dict/' + f_name + '.json'
        with open(path, 'w') as f:
            json.dump(word_df_dict, f)
    if num_of_achievement:
        with open('../../../../RAD/temp/progress_' + f_name + '.pickle', 'wb') as f:
            pickle.dump({'num': num_of_achievement, 'cache': url_cache, 'request': request_url_host_set,
                         'iframe': iframe_src_set, 'link_host': link_set}, f)
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
        wa_file('../../' + file_name, text)
    for file_name, value in write_file_to_alertdir.items():
        text = ''
        for i in value:
            if type(i) == list:
                if not os.path.exists('../../../alert/' + file_name):
                    text += i[0] + '\n'
                text += i[1] + '\n'
            else:
                text += i + '\n'
        wa_file('../../../alert/' + file_name, text)


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
        dic = write_file_to_alertdir
        lock = wfta_lock
    # 各辞書は、ファイル名：[内容, 内容, ...]になるように
    with lock:
        if key.endswith('.csv'):         # csvファイルの場合、contentはリストで[ヘッダ, 内容]となっている
            if key not in dic:
                dic[key] = [content]     # csvファイルの一行目はヘッダも入れる
            else:
                dic[key].append(content[1])   # 1行目以降は、内容だけ入れる
        else:
            if key not in dic:
                dic[key] = [content]
            else:
                dic[key].append(content)   # textファイルの場合は、contentがlistではないため


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


def parser(parse_args_dic):
    global word_df_dict
    host = parse_args_dic['host']
    page = parse_args_dic['page']
    q_send = parse_args_dic['q_send']
    file_type = parse_args_dic['file_type']
    machine_learning_q = parse_args_dic['machine_learning_q']
    use_mecab = parse_args_dic['use_mecab']

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
        if hack_level:    # hackの文字が入っていると0以外が返ってくる
            if hack_level == 1:
                update_write_file_dict('result', 'hack_word_Lv' + str(hack_level) + '.txt', content=page.url)
            else:
                update_write_file_dict('alert', 'hack_word_Lv' + str(hack_level) + '.txt', content=page.url)
        if word_tf_dict is not False:
            with word_df_lock:
                word_df_dict = add_word_dic(word_df_dict, word_tf_dict)  # サーバのidf計算のために単語と出現ページ数を更新
            if word_idf_dict:
                word_tfidf = make_tfidf_dict(idf_dict=word_idf_dict, tf_dict=word_tf_dict)  # tf-idf値を計算
                top10 = get_top10_tfidf(tfidf_dict=word_tfidf)   # top10を取得。ページ内に単語がなかった場合は空リストが返る
                # ハッシュ値が異なるため、重要単語を比較
                #if num_of_days is not True:
                if True:  # 実験のため毎回比較
                    pre_top10 = urlDict.get_top10_from_url_dict(url=page.url)    # 前回のtop10を取得
                    if pre_top10 is not None:
                        symmetric_difference = set(top10) ^ set(pre_top10)         # 排他的論理和
                        if len(symmetric_difference) > 16:
                            update_write_file_dict('alert', 'change_important_word.csv',
                                                   content=['URL,top10,pre', page.url + ',' + str(top10) + ','
                                                            + str(pre_top10)])
                        update_write_file_dict('result', 'symmetric_diff_of_word.csv',
                                               content=['URL,length,top10,pre top10', page.url + ',' +
                                                        str(len(symmetric_difference)) + ',' + str(top10) + ',' +
                                                        str(pre_top10) + ',' + str(num_of_days)])
                urlDict.add_top10_to_url_dict(url=page.url, top10=top10)          # top10を更新

            # ページにあった単語が今までの頻出単語にどれだけ含まれているか調査-------------------------------
            if frequent_word_list:
                # 上位50個と比較し、頻出単語に含まれていなかった単語の数を保存
                max_num = min(len(frequent_word_list), 50)  # 保存されている単語数が50未満のサーバがあるため
                and_ = set(word_tf_dict.keys()).intersection(set(frequent_word_list[0:max_num]))
                update_write_file_dict('result', 'frequent_word_investigation.csv',
                                       ['URL,new', page.url + ',' + str(page.new_page) + ',' + str(len(and_))])

                # 新しいページで、ANDの単語(このページの単語と今までの頻出単語top50とのAND)が5個以下なら
                if len(and_) < 6 and page.new_page:
                    update_write_file_dict('alert', 'new_page_without_frequent_word.csv',
                                           ['URL,num', page.url + ',' + str(and_)])

    # iframeの検査
    iframe_result = iframe_inspection(soup)     # iframeがなければFalse
    if iframe_result:
        if iframe_result['iframe_src_list']:    # iframeのsrc属性値のネットワーク部のリストがあれば
            if not urlDict.compere_iframe(page.url, iframe_result['iframe_src_list']):   # 前回データと比較
                update_write_file_dict('result', 'change_iframeSrc.csv', content=['URL', page.url])
            with iframe_src_set_lock:   # iframeのsrc集合の更新
                iframe_src_set.update(set(iframe_result['iframe_src_list']))
            if iframe_src_set_pre:   # 前回のクローリング時のiframeのsrcデータがあれば
                diff = set(iframe_result['iframe_src_list']).difference(iframe_src_set_pre)   # 差をとる
                if diff:   # 前回のクローリング時に確認されなかったサーバのiframeが使われているならば
                    for i in diff:
                        update_write_file_dict('alert', 'new_iframeSrc.csv',
                                               content=['URL,iframe_src', page.url + ',' + i])
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

    """
    # scriptに関して
    # script名が特徴的かどうか。[(スクリプト名, そのスクリプトタグ),()...]となるリストを返す
    script_names = script_inspection(soup=soup)
    if len(script_names):
        for i, v in script_names:
            update_write_file_dict('result', 'script_name.csv', content=['script name,URL,script', str(i) + ',' +
                                                                         page.url + ',' + str(v)])
    # タイトルにscriptが含まれているかどうか
    title = title_inspection(soup)
    if title:
        update_write_file_dict('result', 'script_in_title.csv', content=['URL', page.url])
    """

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
        host_set = set([urlparse(url).netloc for url in page.normalized_links])  # リンク集からホスト名だけの集合を作成
        with link_set_lock:  # リンク集合の更新
            link_set.update(host_set)
        if link_set_pre:  # 前回のデータがあれば
            diff = host_set.difference(link_set_pre)  # 差をとる
            if diff:  # 今まで確認されなかったサーバへのリンクが貼られていれば
                temp = list()
                for link_host in diff:   # ページのリンク集から、特定のホスト名を持つURLを取ってくる
                    temp.extend([check_url for check_url in page.normalized_links if link_host in check_url])
                for i in temp:
                    update_write_file_dict('alert', 'link_to_new_server.csv', content=['URL,link', page.url + ',' + i])

    # スレッド集合から削除
    try:
        threadId_set.remove(threading.get_ident())   # del_thread()で消されていた場合、KeyErrorになる
        del threadId_time[threading.get_ident()]
    except KeyError as e:
        print(host + ' : ' + 'thread was deleted. : ' + page.url + ' : ' + str(e))


# 180秒以上続いているスレッドのリストを返す
def check_thread_time(now):
    thread_list = list()
    for threadId, th_time in threadId_time.items():
        if (now - th_time) >= 180:
            thread_list.append(threadId)
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


# 10秒間受信キューに何も入っていなければFalseを返す
def receive(recv_r, send_r):
    try:
        temp_r = recv_r.get(block=True, timeout=10)
    except Exception:
        return False
    send_to_parent(send_r, 'receive')
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
    phantomjs = args_dic['phantomjs']
    use_mecab = args_dic['mecab']

    # PhantomJSを使うdriverを取得、一つのプロセスは一つのPhantomJSを使う
    if phantomjs:
        driver = driver_get()
        if driver is False:
            os._exit(0)

    page = None

    # 保存データのロードや初めての場合は必要なディレクトリの作成などを行う
    init(host, screenshots)

    # 180秒以上パースに時間がかかるスレッドは削除する(ためのスレッド)
    t = threading.Thread(target=del_thread, args=(host,))
    t.daemon = True
    t.start()

    # クローラプロセスメインループ
    while True:
        # 動いていることを確認
        if page is None:
            print(host + ' : main loop is running...')
        else:
            print(host + ' : ' + str(page.url_initial))

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
        search_tuple = receive(q_recv, q_send)      # URLが10秒間届かなければFalse
        if search_tuple is False:
            if threadId_set:   # 実行中のパーススレッドがあるならば
                print(host + ' : wait 3sec because the queue is empty.')
                sleep(3)   # 3秒待って、もう一度受信キューを確認する
                continue
            else:   # パーススレッドが全て終わっていれば、メインループを抜ける
                break

        # 検索するURLを取得
        url, url_src = search_tuple  # 親から送られてくるURLは、(URL, リンク元URL)のタプル
        if url in url_cache:    # 既にクローリング済ならば次へ。
            continue           # ここに当てはまるのは、NOT FOUNDページとかリダイレクトされた後のURLとか？

        # Pageオブジェクトを作成
        page = Page(url, url_src)

        # urlopenで接続
        urlopen_result = page.set_html_and_content_type_urlopen(page.url)
        if type(urlopen_result) == list:  # istが返るとエラー
            update_write_file_dict('host', urlopen_result[0]+'.txt', content=urlopen_result[1])
            continue
        if page.url in url_cache:   # urlopenでurlが変わっている可能性があるため再度チェック
            continue

        # リダイレクトのチェック
        redirect = check_redirect(page, host)
        if redirect is True:   # 別サーバへリダイレクトしていればTrue
            send_to_parent(q_send, {'type': 'redirect', 'url_tuple_list': [(page.url, page.src, page.url_initial)]})
            continue
        if redirect == "same":    # 同じホスト内のリダイレクトの場合、処理の続行を親プロセスに通知
            send_to_parent(sendq=q_send, data=(page.url, "redirect"))

        # content-typeからウェブページ(str)かその他ファイル(False)かを判断
        file_type = page_or_file(page)
        update_write_file_dict('host', 'content-type.csv', ['content-type,url,src',
                                                            page.content_type + ',' + page.url + ',' + page.src])  # 記録

        if type(file_type) == str:   # ウェブページの場合
            if phantomjs:
                # phantomJSでURLに再接続。関数内で接続後１秒待機
                phantom_result = set_html(page=page, driver=driver)
                if type(phantom_result) == list:     # 接続エラーの場合はlistが返る
                    update_write_file_dict('host', phantom_result[0] + '.txt', content=phantom_result[1])
                    driver.quit()           # driverを一回終了して
                    driver = driver_get()   # 再取得
                    if driver is False:
                        os._exit(0)
                    else:
                        phantom_result = set_html(page=page, driver=driver)   # もっかい接続を試してみる
                        if type(phantom_result) == list:                # ２回目もエラーなら次のURLへ(諦める)
                            continue
                if page.url in url_cache:     # phantomJSでurlが変わっている可能性があるため再度チェック
                    continue

                # リダイレクトのチェック
                redirect = check_redirect(page, host)
                if redirect is True:    # リダイレクトでサーバが変わっていれば
                    send_to_parent(q_send, {'type': 'redirect',
                                            'url_tuple_list': [(page.url, page.src, page.url_initial)]})
                    continue
                if redirect == "same":   # URLは変わったがサーバは変わらなかった場合は、処理の続行を親プロセスに通知
                    send_to_parent(sendq=q_send, data=(page.url, "redirect"))
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
                            update_write_file_dict('alert', 'new_request_url.txt', content=page.url + ',' + str(diff))
                if test:
                    wa_file('../../method_except_forGETPOST.csv', page.url + ',' + page.src + ',' + str(test) + '\n')

                # スクショが欲しければ撮る
                if screenshots:
                    try:
                        if phantom_result is True:
                            driver.save_screenshot('../../../../image/' + dir_name + '/' +
                                                   str(len(os.listdir('../../../../image/' + dir_name))) + '.png')
                    except Exception as e:
                        print(e)

                # 別窓やタブが開いた場合、そのURLを取得
                try:
                    window_url_list = get_window_url(page, driver)
                except Exception as e:
                    wa_file('../../window_url_get_error.text', data=page.url + '\n' + str(e) + '\n')
                else:
                    if window_url_list:   # URLがあった場合、リンクURLを渡すときと同じ形にして親プロセスに送信
                        url_tuple_list = list()
                        for url_temp in window_url_list:
                            url_tuple_list.append((url_temp, page.url))   # 作成タプルはリンクリストを作る時と同じ(URL, src)
                        send_to_parent(q_send, {'type': 'new_window_url', 'url_tuple_list': url_tuple_list})

            # スレッドを作成してパース開始(phantomJSで開いたページのHTMLソースをスクレイピングする)
            parser_thread_args_dic = {'host': host, 'page': page, 'q_send': q_send, 'file_type': file_type,
                                      'machine_learning_q': machine_learning_q, 'use_mecab': use_mecab}
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
        if not (num_of_achievement % 300):  # 300URLをクローリングごとに保存して終了
            print(host + ' : achievement have reached ' + str(num_of_achievement))
            while threadId_set:
                print(host + ' : wait 3sec for thread end.')
                sleep(3)
            break

    if page is not None:
        url_cache.add(page.url_initial)  # 親から送られてきたURL
        url_cache.add(page.url_urlopen)  # urlopenで得たURL
        url_cache.add(page.url)          # 最終的にパースしたURL
    save_result()
    print(host + ' saved.')
    try:
        driver.quit()
    except Exception:
        pass
    os._exit(0)
