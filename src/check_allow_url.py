﻿from threading import Thread, Lock
import socket
from urllib.parse import urlparse
from time import sleep


# クローリングするURLかどうかを判定するスレッド
# もともとは全フィルタのチェックをスレッドでしていたが、今はIPアドレスのチェックだけ。
class CheckSearchedIPAddressThread(Thread):
    def __init__(self, url_tuple, run_time, ip_address_dict):
        super(CheckSearchedIPAddressThread, self).__init__()
        self.url_tuple = url_tuple
        self.url_host = urlparse(url_tuple[0]).netloc
        if "allow" in ip_address_dict:
            self.IPAddress_allow = ip_address_dict["allow"]
        else:
            self.IPAddress_allow = list()
        self.result = run_time
        self.lock = Lock()

    def run(self):
        self.lock.acquire()   # 最後にacquireするときに自身でデッドロックをかけるため
        crawling_flag = False

        # 組織IPアドレスじゃなければ、"Unknown"
        if self.IPAddress_allow:
            try:
                o = socket.getaddrinfo(self.url_host, 80, 0, 0, proto=socket.IPPROTO_TCP)
            except Exception as e:
                # wa_file('get_addinfo_e.csv', check_url + ',' + self.url_tuple[1] + ',' + str(e) + '\n')
                # crawling_flag = check_url + ',' + self.url_tuple[1] + ',' + str(e) + '\n'
                crawling_flag = "Unknown"
            else:
                ip_address = o[0][4][0]
                for ip in self.IPAddress_allow:
                    if ip_address.startswith(ip):  # ipアドレスにより組織関連サーバだと判断
                        # crawling_flag = True  したが、立命は多すぎるので検索はしない
                        # w_file('ipAddress_ritsumei.csv', check_url + ',' + self.url_tuple[1] + '\n')
                        crawling_flag = 'Black'  # ブラックリストに引っかかったことにする
                        break
        self.result = crawling_flag
        self.lock.acquire(timeout=120)   # runの一行目でacquireしているので、メインスレッドでreleaseされるまでデッドロックがかかる


# filtering_dictで調べて、接続許可が出ればTrue、拒否されればFalseかstr
# IPアドレスのチェックまでするなら、thread Object が返る。
def check_searched_url(url_tuple, run_time, filtering_dict, special_white=None):
    domain_allow = filtering_dict["DOMAIN"]["allow"]
    domain_deny = filtering_dict["DOMAIN"]["deny"]
    white = filtering_dict["WHITE"]
    black = filtering_dict["BLACK"]

    check_url = url_tuple[0]
    url_host = urlparse(check_url).netloc
    url_path = urlparse(check_url).path

    if not url_host:  # URL内に「://」がなかった場合
        return False
    else:
        # 組織外URLはFalse. 組織内だがブラリスの場合は'black'、 不明の場合は'unknown'

        # リンクやリクエストの特別なホワイトリストがあれば
        if special_white:
            for white_host, white_path_list in special_white.items():
                if url_host.endswith(white_host) and \
                        [wh_pa for wh_pa in white_path_list if url_path.startswith(wh_pa)]:
                    return "Special"   # 過去に外部としてアラートされたが、ホワイトリストに追加されてそれに引っかかったもの(安全な外部URL)

        # ホワイトリストはホスト名は組織ではないが、URLが途中まで一致したら接続を許可する
        for white_host, white_path_list in white.items():
            if url_host.endswith(white_host) and \
                    [wh_pa for wh_pa in white_path_list if url_path.startswith(wh_pa)]:
                return True

        # 外部ドメインなので許可しない
        if [not_domain for not_domain in domain_deny if url_host.endswith(not_domain)]:
            return False

        # 内部ドメインだが、ブラックリストに載っているので許可しない
        if [black_string for black_string in black if black_string in check_url]:
            return 'Black'

        # 組織ドメインなら許可
        if [crawling_domain for crawling_domain in domain_allow if url_host.endswith(crawling_domain)]:
            return True

    # IPアドレスのチェックをする (そもそもホスト名だけを指定してくれていれば、このスレッドは作らなくていい)
    if filtering_dict["IPAddress"]:
        t = CheckSearchedIPAddressThread(url_host, run_time, filtering_dict["IPAddress"], )
        t.setDaemon(True)  # daemonにすることで、メインスレッドはこのスレッドが生きていても死ぬことができる
        try:
            t.start()
        except RuntimeError:
            return "Unknown"
        else:
            return t

    return False


# url_listのURLが安全かどうかをフィルタを使って確かめる
# 診断が終わったURLの集合。 要素はタプル(url, "診断結果")
def inspection_url_by_filter(url_list, filtering_dict, special_filter=None):
    result_set = set()
    thread_set = set()
    for url in url_list:
        res = check_searched_url(url_tuple=(url, ""), run_time=0, filtering_dict=filtering_dict,
                                 special_white=special_filter)
        if type(res) == CheckSearchedIPAddressThread:
            thread_set.add(res)
        else:
            res = (url, res)
            result_set.add(res)

    # IPアドレスのチェックが行われているスレッドが終わるまで最大10秒待つ  (立命クローリングではIPアドレスを設定していないので実行されない)
    if thread_set:
        for i in range(10):
            rm_list = list()
            for thread in thread_set:
                if type(thread.result) is not int:
                    res = (thread.url_tuple[0], thread.result)
                    result_set.add(res)
                    rm_list.append(thread)
                    thread.lock.release()
            # 評価が終わったスレッドを削除
            for thread in rm_list:
                thread_set.remove(thread)
            if not thread_set:
                break
            sleep(1)

    return result_set
