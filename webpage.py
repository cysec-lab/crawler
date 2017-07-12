from urllib.parse import urlparse, quote
from urllib.request import urlopen
from time import sleep
from copy import deepcopy
from content_get import UrlOpenReadThread


# 一つのURLが持つ情報をまとめたもの
# メソッドは自分のプロパティを設定するもの(PhantomJSを使わずに)
# PhantomJSを使うメソッドは別ファイルに関数としてまとめている
class Page:
    def __init__(self, url, src):
        self.url_initial = url         # 親プロセスから送られてきたURL
        self.src = src                 # このURLが貼られていたリンク元URL
        self.url_urlopen = None       # urlopenで接続したURL
        self.content_type = None      # このURLのcontent-type。urlopen時のヘッダから取得
        self.content_length = None    # ファイルサイズ。urlopen時にヘッダから取得
        self.encoding = 'utf-8'        # 文字コード。urlopen時のヘッダから取得(使っていない
        self.html_urlopen = None      # urlopenで取得したHTMLソースコード(使っていない
        self.url = url                 # current_url。urlopen、phantomsJSで接続した後にそれぞれ更新
        self.html = None              # HTMLソースコード。urlopen、phantomsJSで接続した後にそれぞれ更新
        self.hostName = None          # urlopen、phantomsJSで接続した後にそれぞれ更新
        self.scheme = None            # 上と同じ
        self.links = set()             # このページに貼られていたリンクURLの集合。HTMLソースコードから抽出。
        self.normalized_links = set()  # 上のリンク集合のURLを正規化したもの(http://をつけたりなんやらしたり)
        self.request_url = list()              # このページをロードするために行ったリクエストのURLのリスト。PhantomJSのログから
        self.request_url_host = list()         # 上のURLからホスト名だけ抜き出したもの
        self.request_url_same_server = list()  # ２個上のURLから、同じサーバ内のURLを抜き出したもの
        self.loop_escape = False    # 自身に再帰する関数があるのでそこから抜け出す用

    def set_html_and_content_type_urlopen(self, url):
        try:
            content = urlopen(url=url, timeout=10)   # レスポンスのtimeoutは10秒
            sleep(1)
        except UnicodeEncodeError as e:   # URLに日本語が混ざっている場合にたまになる
            if self.loop_escape:
                return ['unicodeEncodeError_urlopen', self.url + '\n' + str(e)]    # utf-8でもだめならあきらめる
            url_temp = quote(url, safe=':/', encoding='utf-8')    # utf-8で変えてもう一度すると接続できるときがある
            self.loop_escape = True
            return self.set_html_and_content_type_urlopen(url_temp)
        except Exception as e:
            return ['Error_urlopen', self.url + '\n' + str(e)]
        else:
            t = UrlOpenReadThread(content)
            t.daemon = True
            t.start()
            t.join(timeout=60)  # 60秒のread待機時間
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
            self.url = self.url_urlopen
            if self.content_type is None:
                self.content_type = ''
            self.hostName = urlparse(self.url).netloc
            self.scheme = urlparse(self.url).scheme
        return True

    def make_links_html(self, soup):
        bs_html = soup
        for a_area in bs_html.findAll('a'):      # aタグを全部取ってくる
            link_url = a_area.get('href')
            style = a_area.get('class')
            if link_url:
                if ('#' == link_url) or ('/' == link_url):
                    continue
                if 'styleswitch' in str(style):
                    continue
                else:
                    if ('mailto:' not in link_url)and('do=login' not in link_url)and('tel:' not in link_url):
                        self.links.add(link_url)

    def make_links_xml(self, soup):
        bs_xml = soup
        link_1 = bs_xml.findAll('link')     # linkタグではさまれている部分をリストで返す
        i = 0
        # httpから始まり、</link>か空白までの文字をURLとして保存
        while True:
            if i == len(link_1):
                break
            row = str(link_1[i])
            exist_http = row.find('http')
            if exist_http != -1:
                row = row[exist_http:]
                if row.find('</link>'):
                    temp = row.find('</link>')
                    row = row[0:temp]
                self.links.add(row)
            i += 1

    # http以外から始まるurl_1をroot_1で補完
    # むっちゃごちゃごちゃしてるけど、立命のリンクは汚いので普通の正規化関数では正規化できなかった
    def comp_http(self, root_1, url_1):
        if url_1.startswith('./'):       # ./から始まっていると./を削除
            url_1 = url_1[2:]
        if root_1.endswith('/'):         # 最後が / (ディレクトリ名)なら削除
            root_2 = root_1[0:-1]
        elif root_1 == self.scheme + '://' + self.hostName:  # ルートがホスト名ならそのまま
            root_2 = root_1
        else:                      # root_1のURLがファイル名を指しているためディレクトリを指す様に変更
            root_2 = root_1
            slash = root_2.rfind('/')
            root_2 = root_2[0:slash]
        # root2はurlをリンクしていた元ページのURL。最後が/やファイル名ならそれを削除した
        if root_2 == self.scheme + '://' + self.hostName:
            temp = ['', '', self.hostName, '']
        else:
            temp = root_2.split('/')
        # tempはホスト名から一つ上のディレクトリまでを参照するため
        if url_1.startswith('//'):
            return self.scheme + ':' + url_1
        elif url_1.startswith('/'):
            return self.scheme + '://' + self.hostName + url_1
        elif url_1.startswith('#'):
            return '#'
        elif url_1.startswith('..'):
            url_2 = url_1[3:]
            return self.comp_http(self.scheme + '://' + '/'.join(temp[2:-1]) + '/', url_2)
        # javascriptの文字から始まるものも正規化されてURLとされる
        if url_1.startswith('JavaScript:') or url_1.startswith('Javascript:')\
                or url_1.startswith('JAVASCRIPT:') or url_1.startswith('javascript:'):
            return '#'
        return root_2 + '/' + url_1

    # リンク集にあるURLを補完し、正規化したリンク集を作成する
    def complete_links(self, html_special_char):
        temp_set = deepcopy(self.links)
        while temp_set:
            # リンク集合からpop
            checked_url = temp_set.pop()
            checked_url = checked_url.strip()

            # 'http'から始まっていなければ、self.urlから補完する(http://.../を付けたす)
            if not (checked_url.startswith('http')):
                checked_url = self.comp_http(self.url, checked_url)
                if checked_url == '#':   # 'javascript:'から始まるものや'#'から始まるもの
                    continue
            # 特殊文字が使われているものは置き換える
            for spechar in html_special_char:
                checked_url = checked_url.replace(spechar[0], spechar[1])

            # #が含まれていたら、#手前までのURLにする
            sharp = checked_url.find('#')
            if not (sharp == -1):
                checked_url = checked_url[0:sharp]

            # /./が含まれていたら./を消す
            if '/./' in checked_url:
                checked_url = checked_url.replace('/./', '/')

            # /..が含まれていたらパスを1つ上げて処理する (例： http://www.jp/dir/dir2/../html  -->  http://www.jp/dir/html
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

            # ?&は?に置き換える(いくつかのサイトで「http://www.ac.jp/?&変数=値」のような書き方がある(apu))
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
                        time_temp = checked_url.find('time=')
                        if not (time_temp == -1):
                            time_str = checked_url[time_temp + 5:]
                            for i in range(len(time_str)):
                                if not time_str[i].isdigit():
                                    break
                            checked_url = checked_url[0:time_temp + 5] + '0' + checked_url[time_temp + 5 + i:]
                        # URLにcaldate= で日付が設定されている場合、2015-2017年の間以外のものを排除する (apuのサイト)
                        # URLにdate= で日付が設定されている場合、2015-2017年の間以外のものを排除する (スポ健のブログ)
                        checked_url_temp = checked_url.replace('-', '')  # スポ健はdate=2016-08-08みたいになっているため
                        date_start = checked_url_temp.find('date=')
                        if not (date_start == -1):
                            try:
                                date_int = int(checked_url[date_start + 5: date_start + 9])
                            except:
                                pass
                            else:
                                if (2015 < date_int) and (date_int < 2017):
                                    pass
                                else:
                                    continue
                else:  # ?の数が複数存在するため、?までのURLにする
                    checked_url = checked_url[0:checked_url.find('?')]
            if urlparse(checked_url).path == '':  # http://www.ritsumei.ac.jp を
                checked_url += '/'  # http://www.ritsumei.ac.jp/ にする

            # 追加
            self.normalized_links.add(checked_url)
