from threading import Thread, Lock
import socket
from urllib.parse import urlparse
from file_rw import wa_file


# クローリングするURLかどうかを判定するスレッド
class CheckSearchedUrlThread(Thread):
    def __init__(self, url_tuple, run_time, necessary_list):
        super(CheckSearchedUrlThread, self).__init__()
        self.url_tuple = url_tuple
        self.white_list = necessary_list['white_list']
        self.not_domain_list = necessary_list['not_domain_list']
        self.black_list = necessary_list['black_list']
        self.domain_list = necessary_list['domain_list']
        self.IPAddress_list = necessary_list['IPAddress_list']
        self.result = run_time
        self.lock = Lock()

    def run(self):
        self.lock.acquire()   # 最後にacquireするときに自身でデッドロックをかけるため

        host_name = urlparse(self.url_tuple[0]).netloc

        if not host_name:      # URL内に「://」がなかった場合
            ritsumei_flag = False
        else:
            check_url = self.url_tuple[0]
            ritsumei_flag = True
            # 組織外URLはFalseに書き換える。組織内だがブラリスの場合は'black'に、不明の場合は'unknown'に書き換える.
            for i in range(1):
                for white in self.white_list:  # ホワイトリストはホスト名は組織ではないが、URLが途中まで一致したら接続可とする
                    white_host = white.split('+')[0]               # ホワイトリストは"host+/path/"となっている
                    white_url = white_host + white.split('+')[1]
                    if white_host in host_name:
                        if white_url in check_url:
                            ritsumei_flag = False         # 一度falseを入れた後、もう一度trueを入れてループから抜ける
                            break
                if ritsumei_flag is False:
                    ritsumei_flag = True
                    break
                for not_list in self.not_domain_list:    # 立命館ではないと分かっているため、ファイルに出力しない
                    if not_list in host_name:       # 立命館関連のサイトが多すぎて、外部だと判断されたものを
                        ritsumei_flag = False           # 出来る限り目で見て本当に外部か判断していたため。それの作業用。
                        break
                if ritsumei_flag is False:
                    break
                for not_list in self.black_list:  # 検索システムなど(ブラックリスト)を避ける
                    if not_list in check_url:
                        ritsumei_flag = 'black'
                        break
                if ritsumei_flag == 'black':
                    break
                # ドメイン名が設定されているものと完全一致ならば('=='を'in'に変えると含むならばに変えられる)
                for ritsu_domain in self.domain_list:
                    if ritsu_domain in host_name:
                        ritsumei_flag = False
                        break
                if ritsumei_flag is False:
                    ritsumei_flag = True
                    break
                # IPアドレスが登録されているもので始まるかどうか(立命では検索はしない
                if self.IPAddress_list:
                    try:
                        o = socket.getaddrinfo(host_name, 80, 0, 0, proto=socket.IPPROTO_TCP)
                    except Exception as e:
                        wa_file('get_addinfo_e.csv', check_url + ',' + self.url_tuple[1] + ',' + str(e) + '\n')
                        ritsumei_flag = 'unknown'
                    else:
                        ip_address = o[0][4][0]
                        for ip in self.IPAddress_list:
                            if not ip_address.startswith(ip):
                                # ipアドレスが133.19.で始まらず(もしくは取得できず)、立命館リストにも載っていなかったので
                                ritsumei_flag = False
                                # wa_file('ritsumeikan_checklist.csv', check_url + ',' + url_tuple[1] + '\n')
                            else:
                                wa_file('ipAddress_ritsumei.csv', check_url + ',' + self.url_tuple[1] + '\n')
                                ritsumei_flag = 'black'   # ipアドレスにより組織関連サーバだと判断(したが、検索はしない
                                break
        self.result = ritsumei_flag
        self.lock.acquire(timeout=120)   # メインスレッドでreleaseされるまで待機
