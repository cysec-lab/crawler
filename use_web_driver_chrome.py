from selenium.webdriver.chrome.options import Options
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from urllib.parse import urlparse
from copy import deepcopy
from content_get_chrome import ChromeGetThread, DriverGetThread
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


# phantomJSを使うためのdriverを返す
def driver_get(screenshots=False, user_agent=''):
    # headless chromeの設定
    options = Options()
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
    # user agent
    if user_agent:
        options.add_argument('--user-agent=' + user_agent)
    # ウィンドウサイズ
    options.add_argument('--window-size=1280,1024')
    # 言語
    options.add_argument('--lang=ja')

    # dlに必要？
    options.add_experimental_option('prefs', {
        'download.default_directory': '../DownloadByChrome',
        'download.prompt_for_download': False,   # ダウンロードの時に確認画面を出さない?
    })

    # コンソールログを取得するために必要
    d = DesiredCapabilities.CHROME
    d['loggingPrefs'] = {'browser': 'ALL', 'driver': 'ALL'}

    # テスト
    options.add_argument('--log-level=0')
    options.add_argument('--allow-file-access-from-files')
    options.add_extension('/home/hiro/Desktop/NetworkWatcher.crx')

    # Chromeのドライバを取得。ここでフリーズしていることがあったため、スレッド化した
    try:
        t = DriverGetThread(options, d)
        # t.daemon = True
        t.start()
        t.join(10)
    except Exception:
        sleep(10)
        try:
            t = DriverGetThread(options, d)
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


def set_html(page, driver):
    try:
        t = ChromeGetThread(driver, page.url)
        t.start()
        t.join(timeout=60)   # 60秒のロード待機時間
    except Exception:
        # スレッド生成時に run timeエラーが出たら、10秒待ってもう一度
        sleep(10)
        try:
            t = ChromeGetThread(driver, page.url)
            t.start()
            t.join(timeout=60)  # 60秒のロード待機時間
        except Exception as e:
            return ['makeThreadError_chrome', page.url + '\n' + str(e)]

    re = True
    if t.re is False:
        re = 'timeout'
    elif t.re is not True:
        return ['Error_chrome', page.url + '\n' + str(t.re)]

    # 読み込み、リダイレクト待機、連続アクセス防止の1秒間
    # sleep(1)
    current_url = driver.current_url
    relay_url = list()
    for i in range(10):
        if current_url != driver.current_url:  # 0.1秒ごとにURLを監視
            current_url = driver.current_url
            relay_url.append(current_url)
        sleep(0.1)
    if set(relay_url).difference({driver.current_url}):  # 最後のURL以外に中継URLがあれば、保存
        page.relay_url = deepcopy(relay_url)

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


def set_request_url(page, driver):
    try:
        print(driver.get_log('browser'))
        print(driver.get_log('driver'))
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