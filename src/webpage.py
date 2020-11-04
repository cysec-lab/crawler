from copy import deepcopy
from json import loads
from logging import getLogger
from time import sleep
from typing import Any, Dict, Iterable, Optional, Tuple, Union
from urllib.parse import quote, urlparse
from urllib.request import urlopen

import bs4
from bs4 import BeautifulSoup
from bs4.element import ResultSet

from html_read_thread import UrlOpenReadThread
from utils.location import location

logger = getLogger(__name__)

# 一つのURLが持つ情報をまとめたもの
# メソッドは自分のプロパティを設定するもの(PhantomJSを使わずに)
# ブラウザを使うメソッドは別ファイルに関数としてまとめている
class Page:
    def __init__(self, url: str, src: str):
        self.url_initial = url         # 親プロセスから送られてきたURL
        self.src = src                 # このURLが貼られていたリンク元URL
        self.url_urlopen: Optional[str] = None        # urlopenで接続したURL
        self.content_type: str = ""       # このURLのcontent-type。urlopen時のヘッダから取得
        self.content_length = None     # ファイルサイズ。urlopen時にヘッダから取得
        self.encoding: str = 'utf-8'        # 文字コード。urlopen時のヘッダから取得(使っていない
        self.html_urlopen: Optional[str] = None       # urlopenで取得したHTMLソースコードのバイト列(使っていない
        self.url: str = url                 # current_url。urlopen、ブラウザで接続した後にそれぞれ更新
        self.html: Optional[str] = None               # HTMLソースコード。urlopen、ブラウザで接続した後にそれぞれ更新
        self.hostName: Optional[str] = None          # urlopen、ブラウザで接続した後にそれぞれ更新
        self.scheme: Optional[str] = None             # 上と同じ
        self.links = set()             # このページに貼られていたリンクURLの集合。HTMLソースコードから抽出。
        self.normalized_links: set[str] = set()  # 上のリンク集合のURLを正規化したもの(http://をつけたりなんやらしたり)
        self.request_url = set()              # このページをロードするために行ったリクエストのURLの集合。
        # self.request_url_host = set()         # 上のURLからホスト名だけ抜き出したもの
        # self.request_url_same_host = set()  # ２個上のURLから、同じサーバ内のURLを抜き出したもの
        self.download_info: Dict[str, Dict[str, str]] = dict()  # 自動ダウンロードがされた場合、ここに情報を保存する
        self.loop_escape = False    # 自身に再帰する関数があるのでそこから抜け出す用
        self.new_page = False
        self.among_url: list[str] = list()   # リダイレクトを1秒以内に複数回されると、ここに記録する。
        self.watcher_html: Optional[list[str]] = None  # watcher.htmlは拡張機能が集めた情報が載っている専用ページ。そのHTML文を保存する。
        self.alert_txt: list[str] = list()   # alertがポップアップされると、そのテキストを追加していく


    def extracting_extension_data(self, soup: bs4.element.Tag):
        """
        拡張機能により追記したDOM要素を除き、別の変数に格納する
        専用HTMLに情報を載せることにした
        """
        # classがRequestとDownloadの要素を集める
        request_elements: list[ResultSet] = soup.find_all('p', attrs={'class': 'Request'})
        download_elements: list[ResultSet] = soup.find_all('p', attrs={'class': 'Download'})
        history_elements: list[ResultSet] = soup.find_all('p', attrs={'class': 'History'})

        # リクエストURLを集合に追加し、同じサーバ内のURLはまるまる保存、それ以外はホスト名だけ保存
        self.request_url: set[str] = set([elm.get_text() for elm in request_elements]) # type: ignore

        # downloadのURLを辞書のリストにし、soupの中身から削除する
        # download_info["数字"] = { URL, FileName, Mime, FileSize, TotalBytes, Danger, StartTime, Referrer } それぞれ辞書型
        download_info: dict[str, dict[str, str]] = dict()
        for elm in download_elements: # type: ignore
            under: int = elm["id"].find("_") # type: ignore
            key: str = elm["id"][under+1:]
            if key not in download_info:
                download_info[key] = dict()
            if elm["id"][0:under] == "JsonData":
                try:
                    json_data = loads(elm.get_text()) # type: ignore
                except Exception as e:
                    print(location() + str(e), flush=True)
                    download_info[key].update({"FileSize": "None", "TotalBytes": "None", "StartTime": "None",
                                               "Danger": "None"})  # 要素を追加しておかないと、参照時にKeyエラーが出る
                else:
                    download_info[key].update(json_data)
            else:
                download_info[key][elm["id"][0:under]] = elm.get_text() # type: ignore
        self.download_info = deepcopy(download_info)

        # URL遷移が起きた場合、記録する
        url_history: list[str] = [history_element.get_text() for history_element in history_elements] # type: ignore
        if len(url_history) < 2:
            url_history = list()
        self.among_url = url_history.copy()

    def set_html_and_content_type_urlopen(self, url: str, time_out: int)-> Union[list[str], bool, None]:
        # レスポンスのtimeoutを決める(適当)
        if time_out > 40:
            res_time_out = time_out - 30
        else:
            res_time_out = 10
        # requestを投げる
        try:
            content: Any = urlopen(url=url, timeout=res_time_out)
        except UnicodeEncodeError as e:   # URLに日本語が混ざっている場合にたまになる
            sleep(1)
            if self.loop_escape:
                return ['unicodeEncodeError_urlopen', self.url + '\n' + str(e)]    # utf-8でもだめならあきらめる
            url_temp = quote(url, safe=':/', encoding='utf-8')    # utf-8で変えてもう一度すると接続できるときがある
            self.loop_escape = True
            return self.set_html_and_content_type_urlopen(url_temp, time_out)
        except Exception as e:
            sleep(1)
            return ['Error_urlopen', self.url + '\n' + str(e)]
        else:
            sleep(1)
            try:
                t = UrlOpenReadThread(content)
                t.start()
                t.join(timeout=time_out)  # time_out秒のread待機時間
            except Exception:  # thread生成時の run time errorが起きたら
                sleep(10)
                try:
                    t = UrlOpenReadThread(content)
                    t.start()
                    t.join(timeout=time_out)  # time_out秒のread待機時間
                except Exception as e:
                    return ['makeThreadError_urlopen', self.url + ',' + self.src + ',' + str(e)]

            if t.re is False:
                return ['infoGetError_urlopen', self.url + ',' + self.src + ',' + 'time out']
            elif t.re is not True:
                return ['infoGetError_urlopen', self.url + ',' + self.src + ',' + str(t.re)]

            self.encoding = t.content['encoding']
            self.html_urlopen = t.content['html_urlopen']
            self.url_urlopen = t.content['url_urlopen']
            self.content_type = t.content['content_type']
            self.content_length = t.content['content_length']

            self.html = self.html_urlopen
            if self.url_urlopen != None:
                self.url = self.url_urlopen
            else:
                self.url = ''
            if self.content_type is None:
                logger.warning('Content-type is None: %s', self.url)
            self.hostName = urlparse(self.url).netloc # type: ignore
            self.scheme = urlparse(self.url).scheme # type: ignore
        return True

    def make_links_html(self, soup: BeautifulSoup):
        for a_tag in soup.findAll('a'): # type: ignore # aタグを全部取ってくる
            link_url: str = a_tag.get('href')
            class_: str = a_tag.get('class')
            if link_url:
                if 'styleswitch' in str(class_):
                    continue
                self.links.add(link_url)

    def make_links_xml(self, soup: BeautifulSoup):
        link_1: Iterable[ResultSet] = soup.findAll('link')     # linkタグではさまれている部分をリストで返す
        i: int = 0
        # httpから始まり、</link>か空白までの文字をURLとして保存
        while True:
            if i == len(link_1):
                break
            row = str(link_1[i]) # type: ignore
            exist_http = row.find('http')
            if exist_http != -1:
                row = row[exist_http:]
                if row.find('</link>'):
                    temp = row.find('</link>')
                    row = row[0:temp]
                self.links.add(row)
            i += 1


    def comp_http(self, root_1: str, url_1: str) -> str:
        """
        http以外から始まるurl_1をroot_1で補完
        むっちゃごちゃごちゃしてるけど、立命のリンクは適当なものも多いので普通のURL正規化関数では正規化できなかった
        """
        if url_1.startswith('./'):       # ./から始まっていると./を削除
            url_1 = url_1[2:]
        if root_1.endswith('/'):         # 最後が / (ディレクトリ名)なら削除
            root_2 = root_1[0:-1]
        elif root_1 == self.scheme + '://' + self.hostName: # type: ignore  # ルートがホスト名ならそのまま
            root_2 = root_1
        else:                      # root_1のURLがファイル名を指しているためディレクトリを指す様に変更
            root_2 = root_1
            slash = root_2.rfind('/')
            root_2 = root_2[0:slash]
        # root2はurlをリンクしていた元ページのURL。最後が/やファイル名ならそれを削除した
        if root_2 == self.scheme + '://' + self.hostName: # type: ignore
            temp = ['', '', self.hostName, '']
        else:
            temp = root_2.split('/')
        # tempはホスト名から一つ上のディレクトリまでを参照するため
        if url_1.startswith('//'):
            return self.scheme + ':' + url_1 # type: ignore
        elif url_1.startswith('/'):
            return self.scheme + '://' + self.hostName + url_1 # type: ignore
        elif url_1.startswith('#'):
            return '#'
        elif url_1.startswith('..'):
            url_2 = url_1[3:]
            return self.comp_http(self.scheme + '://' + '/'.join(temp[2:-1]) + '/', url_2) # type: ignore
        # javascriptの文字から始まるものも正規化されてURLとされる
        if url_1.startswith('JavaScript:') or url_1.startswith('Javascript:')\
                or url_1.startswith('JAVASCRIPT:') or url_1.startswith('javascript:'):
            return '#'
        return root_2 + '/' + url_1


    def complete_links(self, html_special_char: list[Tuple[str, ...]]):
        """
        リンク集にあるURLを補完し、正規化したリンク集を作成する
        URLにcaldate= で日付が設定されている場合、2016-2019年の間以外のものを排除する (apuのサイト)
        URLにdate= で日付が設定されている場合、2016-2019年の間以外のものを排除する (スポ健のブログ)

        TODO: 日付やカレンダーが無限に続く処理をどうにかする
        """
        temp_set = deepcopy(self.links)
        while temp_set:
            # リンク集合からpop
            checked_url = temp_set.pop()
            checked_url = checked_url.strip()

            # "#" や "/" の一文字の場合
            if ('#' == checked_url) or ('/' == checked_url):
                continue

            # mailto: はメール作成, tel: は電話
            if ('mailto:' in checked_url) or ('tel:' in checked_url):
                continue

            # 'http'から始まっていなければ、self.urlから補完する(http://.../を付けたす)
            if not (checked_url.startswith('http')):
                checked_url = self.comp_http(self.url, checked_url) # type: ignore
                if checked_url == '#':   # 'javascript:'から始まるものや'#'から始まるもの
                    continue
            # 特殊文字が使われているものは置き換える
            included_spechar = [spechar for spechar in html_special_char if spechar[0] in checked_url]
            for spechar in included_spechar:
                checked_url = checked_url.replace(spechar[0], spechar[1])
            # #が含まれていたら、#手前までのURLにする
            sharp = checked_url.find('#')
            if not (sharp == -1):
                checked_url = checked_url[0:sharp]

            # /./が含まれていたら./を消す -> http://www.ritsumei.ac.jp/home/./index.htmlみたいなURLが見つかる
            if '/./' in checked_url:
                checked_url = checked_url.replace('/./', '/')

            # /..が含まれていたらパスを1つ上げて処理する (例： http://www.jp/dir/dir2/../html  ->  http://www.jp/dir/html
            o = urlparse(checked_url)
            while '/..' in o.path:
                path_list = o.path.split('/')
                path = ''
                for part in path_list:
                    if part == '..':
                        path = path[0:path.rfind('/')]
                    else:
                        path += '/' + part
                path = path[1:]
                checked_url = o.scheme + '://' + o.netloc + path
                o = urlparse(checked_url)

            # パス中に'////...'があると'/'に置き換える
            o = urlparse(checked_url)
            while '//' in o.path:
                checked_url = o.scheme + '://' + o.netloc + o.path.replace('//', '/')
                o = urlparse(checked_url)

            # ?&は?に置き換える(いくつかのサイト(apu)で「http://www.ac.jp/?&変数=値」のような書き方がある)
            if '?&' in checked_url:
                checked_url = checked_url.replace('?&', '?')

            # ?と&、=の数が等しいかチェック、等しければ変数に値が入っているかをチェック
            question = checked_url.count('?')
            if question:
                if question == 1:
                    amp = checked_url.count('&') + 1  # +1 は '?' の分
                    if not (amp == checked_url.count('=')):  # 等しくなければ、?までのURLにする
                        checked_url = checked_url[0:checked_url.find('?')]
                    else:
                        # 変数に値が設定されているかチェック、されていない変数は削除する
                        query = urlparse(checked_url).query
                        if query.find('&&') or query.find('=='):  # &&や==の文字が入っていると面倒なのでアウト。
                            continue  # ブラウザではその変数は無視して実行できるみたい
                        checked_url_temp = checked_url.replace(query, '')
                        query_list = query.split('&')
                        for i in query_list:
                            if not (i.split('=')[1] == ''):
                                checked_url_temp += i + '&'
                        if checked_url_temp.endswith('&'):
                            checked_url = checked_url_temp.rstrip('&')
                        elif checked_url_temp.endswith('?'):
                            checked_url = checked_url_temp.rstrip('?')
                        # URLにtime= で時間が設定されているものがあった。time=0にパラメータを書き換える
                        time_temp: int = checked_url.find('time=')
                        if not (time_temp == -1):
                            time_str = checked_url[time_temp + 5:]
                            for i in range(len(time_str)):
                                if not time_str[i].isdigit():
                                    break
                            checked_url: str = checked_url[0:time_temp + 5] + '0' + checked_url[time_temp + 5 + i:] # type: ignore
                        # URLにcaldate= で日付が設定されている場合、2016-2019年の間以外のものを排除する (apuのサイト)
                        # URLにdate= で日付が設定されている場合、2016-2019年の間以外のものを排除する (スポ健のブログ)
                        checked_url_temp = checked_url.replace('-', '')  # スポ健はdate=2016-08-08みたいになっているため
                        date_start = checked_url_temp.find('date=')
                        if not (date_start == -1):
                            try:
                                date_int = int(checked_url[date_start + 5: date_start + 9])
                            except:
                                pass
                            else:
                                if (2016 < date_int) and (date_int < 2019):
                                    pass
                                else:
                                    continue
                else:  # ?の数が複数存在するため、?までのURLにする
                    checked_url = checked_url[0:checked_url.find('?')]
            if urlparse(checked_url).path == '':  # http://www.ritsumei.ac.jp を
                checked_url += '/'  # http://www.ritsumei.ac.jp/ にする

            # 追加
            self.normalized_links.add(checked_url)
