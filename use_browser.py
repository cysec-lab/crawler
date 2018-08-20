from time import sleep
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from FirefoxProfile_new import FirefoxProfile
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from urllib.parse import urlparse
from copy import deepcopy
from get_web_driver_thread import GetChromeDriverThread, GetFirefoxDriverThread, GetPhantomJSDriverThread
from html_read_thread import WebDriverGetThread


# Firefoxを使うためのdriverを返す
# ファイルダウンロード可能?
# RequestURLの取得可能(アドオンを用いて)
# ログコンソールの取得不可能(アドオンの結果は</body>と</html>の間にはさむことで、取得する)
def get_fox_driver(screenshots=False, user_agent=''):
    # headless FireFoxの設定
    options = FirefoxOptions()
    fpro = FirefoxProfile()

    # ヘッドレスモードに
    options.add_argument('-headless')

    # user agent
    if user_agent:
        fpro.set_preference('general.useragent.override', user_agent)

    # アドオン使えるように
    fpro.add_extension(extension='/home/hiro/Desktop/GetRequest.xpi')

    # ファイルダウンロードできるように
    fpro.set_preference('browser.download.folderList', 2)  # 2:ユーザ定義フォルダ
    fpro.set_preference('browser.download.dir', '../DownloadByFF')
    fpro.set_preference('browser.download.manager.showWhenStarting', False)  # ダウンロードマネージャ起動しないように
    fpro.set_preference('browser.helpApps.alwaysAsk.force', False)
    fpro.set_preference('browser.download.manager.alertOnEXEOpen', False)
    fpro.set_preference('browser.download.manager.closeWhenDone', True)
    fpro.set_preference('browser.helperApps.neverAsk.saveToDisk',
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document')

    # コンソールログを取得するために必要(ffではすべてのログが見れない)
    d = DesiredCapabilities.FIREFOX
    d['loggingPrefs'] = {'browser': 'ALL', 'driver': 'ALL', 'client': 'ALL', 'performance': 'ALL', 'server': 'ALL'}

    # Firefoxのドライバを取得。ここでフリーズしていることがあったため、スレッド化した
    try:
        t = GetFirefoxDriverThread(options=options, d=d, ffprofile=fpro)
        # t.daemon = True
        t.start()
        t.join(10)
    except Exception:
        sleep(10)
        try:
            t = GetFirefoxDriverThread(options=options, d=d, ffprofile=fpro)
            # t.daemon = True
            t.start()
            t.join(10)
        except Exception:
            return False
    if t.re is False:   # ドライバ取得でフリーズしている場合
        quit_driver(t.driver)   # 一応終了させて
        return False
    if t.driver is False:  # 単にエラーで取得できなかった場合
        return False
    driver = t.driver
    driver.set_window_size(1280, 1024)

    return driver


# Chromeを使うためのdriverを返す
# ファイルダウンロードは可能(完了はできたことない。原因不明。)
# RequestURLの取得可能
# ヘッドレスモードでの拡張機能は使用不可
def get_chrome_driver(screenshots=False, user_agent=''):
    # headless chromeの設定
    options = ChromeOptions()
    options.binary_location = "/usr/bin/google-chrome-stable"
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    # # エラーの許容
    options.add_argument('--ignore-certificate-errors')   # 証明書エラーのページを出さない
    options.add_argument('--allow-running-insecure-content')
    # options.add_argument('--disable-web-security')
    # headlessでは不要そうな機能?
    options.add_argument('--disable-desktop-notifications')
    options.add_argument('--disable-hang-monitor')
    options.add_argument('--disable-sync')
    # シークレットモードで起動
    # options.add_argument('--incognito')
    # user agent
    if user_agent:
        options.add_argument('--user-agent=' + user_agent)
    # ウィンドウサイズ
    options.add_argument('--window-size=1280,1024')
    # 言語
    options.add_argument('--lang=ja')

    # dlに必要？
    # iframeを使ったbatファイルのDLはできなかった
    options.add_experimental_option('prefs', {
        'download.default_directory': '../DownloadByChrome',
        'download.prompt_for_download': False,   # ダウンロードの時に確認画面を出さない?
    })

    # コンソールログを取得するために必要
    # browser ： コンソールログ用、　performance : RequestURL用、 driver : driverログ(RequestURLも取れるけどゴミが多いのでperformanceを使う)
    d = DesiredCapabilities.CHROME
    d['loggingPrefs'] = {'browser': 'ALL', 'driver': 'ALL', 'performance': 'ALL'}

    # テスト
    options.add_argument('--log-level=0')
    options.add_argument('--allow-file-access-from-files')
    # options.add_extension('/home/hiro/Desktop/GetRequest.crx')  # ヘッドレスモードでは拡張機能は使えない

    # Chromeのドライバを取得。ここでフリーズしていることがあったため、スレッド化した
    try:
        t = GetChromeDriverThread(options, d)
        # t.daemon = True
        t.start()
        t.join(10)
    except Exception:
        sleep(10)
        try:
            t = GetChromeDriverThread(options, d)
            # t.daemon = True
            t.start()
            t.join(10)
        except Exception:
            return False
    if t.re is False:   # ドライバ取得でフリーズしている場合
        quit_driver(t.driver)   # 一応終了させて
        return False
    if t.driver is False:  # 単にエラーで取得できなかった場合
        return False
    driver = t.driver

    # ダウンロードできるようにするための設定
    # 実際にダウンロードするためにはsleepで待つ必要がある
    driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    driver.execute("send_command", {
        'cmd': 'Page.setDownloadBehavior',
        'params': {
            'behavior': 'allow',
            'downloadPath': '../DownloadByChrome'  # ダウンロード先(ディレクトリがなければ作られる)
        }
    })

    return driver


# phantomJSを使うためのdriverを返す
# ファイルダウンロードは不可能(Windowsならjsを使って出来ないことはない)
# RequestURLのログが残っている
def get_phantom_driver(screenshots, user_agent='*'):
    # PhantomJSの設定
    des_cap = dict(DesiredCapabilities.PHANTOMJS)
    des_cap["phantomjs.page.settings.userAgent"] = user_agent
    if not screenshots:
        des_cap["phantomjs.page.settings.loadImages"] = False
    des_cap['phantomjs.page.settings.resourceTimeout'] = 60   # たぶん意味ない

    # PhantomJSのドライバを取得。ここでフリーズしていることがあったため、スレッド化した
    try:
        t = GetPhantomJSDriverThread(des_cap)
        t.start()
        t.join(10)
    except Exception:
        sleep(10)
        try:
            t = GetPhantomJSDriverThread(des_cap)
            t.start()
            t.join(10)
        except Exception:
            return False

    if t.re is False:   # ドライバ取得でフリーズしている場合
        quit_driver(t.driver)   # 一応終了させて
        return False
    if t.driver is False:  # 単にエラーで取得できなかった場合
        quit_driver(t.driver)   # 一応終了させて
        return False
    driver = t.driver

    # たぶん意味ない
    driver.set_page_load_timeout = 60  # ページを構成するファイルのロードのタイムアウト?
    driver.timeout = 10   # リクエストのタイムアウト?

    return driver


def set_html(page, driver):
    try:
        t = WebDriverGetThread(driver, page.url)
        t.start()
        t.join(timeout=60)   # 60秒のロード待機時間
    except Exception:
        # スレッド生成時に run timeエラーが出たら、10秒待ってもう一度
        sleep(10)
        try:
            t = WebDriverGetThread(driver, page.url)
            t.start()
            t.join(timeout=60)  # 60秒のロード待機時間
        except Exception as e:
            return ['makingWebDriverGetThreadError', page.url + '\n' + str(e)]

    re = True
    if t.re is False:
        re = 'timeout'
    elif t.re is not True:
        return ['Error_WebDriver', page.url + '\n' + str(t.re)]

    # 読み込み、リダイレクト待機、連続アクセス防止の1秒間
    sleep(1)  # ただの1秒待機をやめて、0.1秒待機を10回繰り返すことに
    # chromeでは以下のようにしても、間のリダイレクトを検出することはできなかった。
    # リダイレクトはするが、driver.current_urlに逐一反映していかないみたい。
    """
    というかここのdriver.current_urlでエラー落ちするのでこのままでは使わないほうがよい
    以下の２つのエラー
    http.client.CannotSendRequest: Request-sent
    selenium.common.exceptions.UnexpectedAlertPresentException: Alert Text: None
    selenium.common.exceptions.TimeoutException: Message: timeout
    
    relay_url = list()
    current_url = driver.current_url
    print(current_url)
    for i in range(10):
        latest_url = driver.current_url
        print('0.{}'.format(i), latest_url)
        if current_url != latest_url:  # 0.1秒ごとにURLを監視
            relay_url.append(latest_url)
            current_url = latest_url
        sleep(0.1)
    if set(relay_url).difference({driver.current_url}):  # 最後のURL以外に中継URLがあれば、保存
        page.relay_url = deepcopy(relay_url)
    """

    try:
        wait = WebDriverWait(driver, 5)
        wait.until(expected_conditions.presence_of_all_elements_located)   # ロード完了まで最大5秒待つ(たぶんロードは完了しているのでいらない)
        page.url = driver.current_url    # リダイレクトで違うURLの情報を取っている可能性があるため
        page.html = driver.page_source   # htmlソースを更新
    except Exception as e:
        return ['infoGetError_chrome', page.url + '\n' + str(e)]
    else:
        page.hostName = urlparse(page.url).netloc   # ホスト名を更新
        page.scheme = urlparse(page.url).scheme     # スキームも更新
        if page.html:
            return re   # True or 'timeout'がreに入っている。タイムアウトでもhtmlは取れている.全ファイルのロードができてないだけ？
        else:
            return ['infoGetError_chrome', page.url + '\n']


def set_request_url_chrome(page, driver):
    import json
    request_urls = set()
    download_urls = set()
    try:
        performance_log = driver.get_log('performance')
    except Exception as e:
        print(e)
        raise

    for i, log in enumerate(performance_log):
        try:
            log_message = json.loads(log['message'])  # logのkeyは 'message' と "timestamp"
            message = log_message['message']       # log_messageのkeyは "message" と "webview" (webviewの中身は謎の16進数?)
            # with open('/home/hiro/Desktop/lo.txt', 'a') as f:
            #     f.write("{} \t {}\n".format(message['method'], message['params']))
            if message['method'] == 'Network.requestWillBeSent':  # messageのkeyは "params" と "method"
                u = message['params']['request']['url']
                request_urls.add(u)
                if 'redirectResponse' in message['params']:
                    u = message['params']['redirectResponse']['url']   # ステータスコードによるリダイレクト前のRequestURL
                    request_urls.add(u)
            elif message['method'] == 'Network.responseReceived':   # 一応、responseのURLも取得しておく
                u = message['params']['response']['url']            # requestURLにすべて含まれているはずだが。
                request_urls.add(u)
            elif message['method'] == 'Network.loadingFailed':
                # iframeによるdocxファイルのダウンロードエラーは検知。それ以外の方法でのDLはログに残っていなかった
                if message['params']['errorText'] == 'net::ERR_ABORTED':  # このエラーはファイルダウンロードエラー?
                    searched_id = message['params']['requestId']
                    print(searched_id)
                    for log2 in reversed(performance_log[0:i]):   # エラーログから遡って、同じrequestIDのrequestかresponseを探す
                        message2 = json.loads(log2['message'])['message']
                        print(message2)
                        if message2['method'] == 'Network.requestWillBeSent':
                            if message2['params']['requestId'] == searched_id:   # 見つけると、そのURLを取ってくる
                                download_url = message2['params']['request']['url']
                                download_urls.add(download_url)
                                break
                        elif message2['method'] == 'Network.responseReceived':   # 見つけると、そのURLを取ってくる
                            if message2['params']['requestId'] == searched_id:
                                download_url = message2['params']['response']['url']
                                download_urls.add(download_url)
                                break
        except Exception as e:
            print('error ', e)
    page.request_url = deepcopy(request_urls)
    page.download_url = deepcopy(download_urls)

    # 今保存したURLの中で、同じサーバ内のURLはまるまる保存、それ以外はホスト名だけ保存
    for url in page.request_url:
        url_domain = urlparse(url).netloc
        if page.hostName == url_domain:  # 同じホスト名(サーバ)のURLはそのまま保存
            page.request_url_same_server.append(url)
        if url_domain.count('.') > 2:  # xx.ac.jpのように「.」が2つしかないものはそのまま
            url_domain = '.'.join(url_domain.split('.')[1:])  # www.ritsumei.ac.jpは、ritsumei.ac.jpにする
        page.request_url_host.append(url_domain)  # ホスト名(ネットワーク部)だけ保存


def set_request_url_phantom(page, driver):
    try:
        log_content = driver.get_log('har')[0]['message']
    except Exception as e:
        print(e)
        raise
    temp = set()   # ページをロードするのにリクエストしたurlを入れる集合
    re = list()    # GETとPOST以外のメソッドがあれば入る
    # GETとPOSTのメソッドのURLをpageの属性に保存
    while True:
        get = log_content.find('"method":')
        if get == -1:
            break
        if log_content[get+9: get+14] == '"GET"':
            end = log_content[get + 22:].find('"')
            url_2 = log_content[get + 22: get + 22 + end]
            temp.add(url_2)
        elif log_content[get+9: get+15] == '"POST"':
            end = log_content[get + 23:].find('"')
            url_2 = log_content[get + 23: get + 23 + end]
            temp.add(url_2)
        else:
            # 以下はGETメソッド以外があるかどうか調査するため
            end = log_content[get + 26:].find('"')
            url_2 = log_content[get + 9: get + 26 + end]
            re.append(url_2)
        log_content = log_content[end:]
    page.request_url = deepcopy(temp)

    # 今保存したURLの中で、同じサーバ内のURLはまるまる保存、それ以外はホスト名だけ保存
    for url in page.request_url:
        url_domain = urlparse(url).netloc
        if page.hostName == url_domain:                 # 同じホスト名(サーバ)のURLはそのまま保存
            page.request_url_same_server.append(url)
        if url_domain.count('.') > 2:   # xx.ac.jpのように「.」が2つしかないものはそのまま
            url_domain = '.'.join(url_domain.split('.')[1:])  # www.ritsumei.ac.jpは、ritsumei.ac.jpにする
        page.request_url_host.append(url_domain)     # ホスト名(ネットワーク部)だけ保存
    return re


def get_window_url(driver):
    url_list = list()
    try:
        windows = driver.window_handles
        for window in windows[1:]:
            driver.switch_to.window(window)
            url_list.append(driver.current_url)
            driver.close()
        driver.switch_to.window(windows[0])
    except:
        raise
    return url_list


def take_screenshots(path, driver):
    import os
    try:
        img_name = str(len(os.listdir(path)))
        driver.save_screenshot(path + '/' + img_name + '.png')
    except Exception as e:
        print(e)
    else:
        return True

    return False


def quit_driver(driver):
    try:
        driver.quit()
    except Exception:
        return False
    else:
        return True

"""
def set_content_type(self, driver):
    try:
        har = driver.get_log('har')
    except Exception as e:
        wa_file('../../driverGetLogError.txt', self.url + '\n' + str(e))
        self.content_type = ''
    else:
        message = har[0]['message']
        while True:
            header_start = message.find('"headers":[')
            if header_start == -1:
                self.content_type = ''
                break
            message = message[header_start:]
            header_end = message.find(']')
            header = message[0:header_end]
            start_point = header.find('"name":"Content-Type","value":"')
            if not (start_point == -1):
                start_point += 31
                end_point = header[start_point:].find('"')
                self.content_type = header[start_point: start_point + end_point]
                break
            message = message[header_end:]
            

def click_a_tags(driver, q_send, url_ini):
    try:
        a_tags = driver.find_elements_by_css_selector('a')
    except:
        return 0
    a_tag_length = len(a_tags)
    for i in range(a_tag_length):
        try:
            if not (a_tags[i].get_attribute('onclick') is None):
                if a_tags[i].get_attribute('href') is None:
                    a_tags[i].click()
                    time.sleep(0.5)
                    current_url = driver.current_url
                    if not (current_url == url_ini):
                        send_to_parent(q_send, data=[(current_url, url_ini, 'onclick')])
                        driver.back()
                        time.sleep(0.1)
                        a_tags = driver.find_elements_by_css_selector('a')
        except Exception:
            pass


def download_check(url_ini, url_pjs, host):
    result = None
    if semaphore.acquire(blocking=True, timeout=180):
        try:
            result = os.system('phantomjs ../../../DownloadChecker.js ' + url_ini + ' ' + url_pjs)
        except Exception:
            result = 'Error'
        semaphore.release()
    else:
        wa_file('not_execute_phantomJS.csv', url_ini + ',' + url_pjs + '\n')
    print("result = " + str(result))
    try:
        threadId_set.remove(threading.get_ident())
        del threadId_time[threading.get_ident()]
    except KeyError as e:
        print(host + ' : download_check-function KeyError :' + str(e))
"""