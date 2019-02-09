from time import sleep
import csv
import os
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoAlertPresentException
from selenium.webdriver.common.alert import Alert
from urllib.parse import urlparse

from FirefoxProfile_new import FirefoxProfile
from get_web_driver_thread import GetFirefoxDriverThread
from html_read_thread import WebDriverGetThread
from location import location


# Watcher.htmlのStop Watchingボタンをクリック。拡張機能が監視を終え、収集したデータを記録。
def stop_watcher_and_get_data(driver, wait, watcher_window, page):
    try:
        # watcher.htmlに移動してstopをクリック
        # クリックすると、Watcher.htmlのdivタグ(id="contents")の中に、収集したデータを記録する
        driver.switch_to.window(watcher_window)
        wait.until(expected_conditions.visibility_of_element_located((By.ID, "stop")))
        elm = driver.find_element_by_id("stop")
        elm.click()

        # contentsの最後の要素がDOMに現れるまで待つ
        wait.until(expected_conditions.presence_of_element_located((By.ID, "EndOfData")))

        # watcher.htmlのHTMLをpageインスタンスのプロパテに保存
        page.watcher_html = driver.page_source

        # clearContentsをクリック
        elm = driver.find_element_by_id("clearContents")
        elm.click()
        # 最後の要素が消えるまで待つ
        wait.until(expected_conditions.invisibility_of_element_located((By.ID, "EndOfData")))
    except Exception as e:
        print(location() + str(e), flush=True)
        return False
    else:
        return True


# watcher.htmlのStart Watchingボタンをクリック。拡張機能が監視を始める
def start_watcher_and_move_blank(driver, wait, watcher_window, blank_window):
    try:
        driver.switch_to.window(watcher_window)
        wait.until(expected_conditions.visibility_of_element_located((By.ID, "start")))
        elm = driver.find_element_by_id("start")
        elm.click()
        driver.switch_to.window(blank_window)
        wait.until(lambda d: "Watcher" != driver.title)
    except Exception as e:
        print(location() + str(e), flush=True)
        return False
    else:
        return True


# ページを読み込むためのabout:blankのページを作る。blankページとwatcherページ以外は閉じる
# blankページが作れなければFalse
def create_blank_window(driver, wait, watcher_window):
    blank_window = False
    try:
        driver.switch_to.window(watcher_window)
        wait.until(expected_conditions.visibility_of_element_located((By.ID, "createBlankTab")))
        elm = driver.find_element_by_id("createBlankTab")
        elm.click()
        for i in range(30):
            windows = driver.window_handles
            if len(windows) > 1:
                for window in windows:
                    if watcher_window == window:
                        continue
                    driver.switch_to.window(window)
                    if blank_window is False:
                        if driver.current_url == "about:blank":
                            blank_window = window
                    if window != blank_window:
                        driver.close()
                if blank_window:
                    break
            sleep(0.1)
    except Exception as e:
        print(location() + str(e), flush=True)
        return False
    else:
        return blank_window


# driverを取得した直後に呼ぶ
def get_watcher_window(driver, wait):
    watcher_window = False
    try:
        wait.until(expected_conditions.visibility_of_all_elements_located((By.ID, "button")))
        wait.until(expected_conditions.presence_of_element_located((By.ID, "DoneAttachJS")))
    except TimeoutException as e:
        print(location() + str(e), flush=True)
        return False
    except Exception as e:
        print(location() + str(e), flush=True)
        return False
    try:
        windows = driver.window_handles
        for window in windows:
            driver.switch_to.window(window)
            title = driver.title
            # print("windowId : {}, title : {}".format(window, title), flush=True)
            if title == "Watcher":
                watcher_window = window
            else:
                # print("close : {}".format(window), flush=True)
                driver.close()
    except Exception as e:
        print(location() + str(e), flush=True)   # 最悪、エラーが起きてもwatcher_windowがわかればよい
    try:
        driver.switch_to.window(watcher_window)
    except Exception as e:
        print(location() + str(e), flush=True)
        return False
    else:
        return watcher_window


# Firefoxを使うためのdriverを返す
def get_fox_driver(screenshots=False, user_agent='', org_path=''):
    # headless FireFoxの設定
    options = FirefoxOptions()
    fpro = FirefoxProfile()

    # ヘッドレスモードに
    options.add_argument('-headless')

    # user agent
    if user_agent:
        fpro.set_preference('general.useragent.override', user_agent)

    # アドオン使えるように
    src_dir = os.path.dirname(os.path.abspath(__file__))  # このファイル位置の絶対パスで取得 「*/src」
    extension_dir = src_dir + '/extensions'
    fpro.add_extension(extension=extension_dir + '/CrawlerExtension.xpi')

    # ファイルダウンロードできるように
    if org_path:
        fpro.set_preference('browser.download.folderList', 2)  # 0:デスクトップ　1:Downloadフォルダ 　2:ユーザ定義フォルダ
        fpro.set_preference('browser.download.dir', org_path + '/result/Download')  # なければ作られる
    else:
        fpro.set_preference('browser.download.folderList', 0)
    fpro.set_preference('browser.download.manager.showWhenStarting', False)  # ダウンロードマネージャ起動しないように
    fpro.set_preference('browser.helpApps.alwaysAsk.force', False)
    fpro.set_preference('browser.download.manager.alertOnEXEOpen', False)
    fpro.set_preference('browser.download.manager.closeWhenDone', True)
    # ダウンロード可能なMimeタイプの設定
    mime_list = list()
    mime_file_dir = src_dir + '/files/mime'
    for csv_file in os.listdir(mime_file_dir):
        if not csv_file.endswith(".csv"):
            continue
        try:
            with open(mime_file_dir + "/" + csv_file) as f:
                csv_reader = csv.DictReader(f)
                for row in csv_reader:
                    if row["Template"]:
                        mime_list.append(row["Template"])
        except csv.Error as e:
            print(location() + str(e), flush=True)
    fpro.set_preference('browser.helperApps.neverAsk.saveToDisk', ','.join(mime_list))

    # Firefoxのドライバを取得。ここでフリーズしていることがあったため、スレッド化した
    # メモリが足りなかったらドライバーの取得でフリーズする可能性あり?
    try:
        t = GetFirefoxDriverThread(options=options, ffprofile=fpro)
        t.daemon = True
        t.start()
        t.join(10)
    except Exception as e:     # runtime error とか
        print(location() + str(e), flush=True)
        sleep(10)
        try:
            t = GetFirefoxDriverThread(options=options, ffprofile=fpro)
            t.daemon = True
            t.start()
            t.join(10)
        except Exception:
            return False
    if t.re is False:   # ドライバ取得でフリーズしている場合
        quit_driver(t.driver)   # 一応終了させて
        print("Freeze while getting driver.")
        return False
    if t.driver is False:  # 単にエラーで取得できなかった場合
        print("Error while getting driver.")
        return False
    driver = t.driver
    driver.set_window_size(1280, 1024)

    # 拡張機能のwindowIDを取得し、それ以外のwindowを閉じる
    # geckodriver 0.21.0 から HTTP/1.1 になった？ Keep-Aliveの設定が5秒のせいで、5秒間driverにコマンドがいかなかったらPipeが壊れる.
    # 0.20.1 にダウングレードするか、seleniumを最新にアップグレードすると、 Broken Pipe エラーは出なくなる。
    wait = WebDriverWait(driver, 5)
    watcher_window = get_watcher_window(driver, wait)
    if watcher_window is False:
        print("Couldn't get Watcher Window.")
        return False

    return {"driver": driver, "wait": wait, "watcher_window": watcher_window}


# ブラウザでURLにアクセス、HTMLを取得する
def set_html(page, driver):
    try:
        # URLに接続する(フリーズすることがあるので、スレッドで行う)
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
    if t.re is False:  # Getスレッドがどこかでフリーズしている場合、t.reがFalseのまま
        re = 'timeout'
    elif t.re is not True:  # TrueとFalse以外の場合、GET中にエラー発生
        return ['Error_WebDriver', page.url + '\n' + str(t.re)]

    # レンダリング待機、連続アクセス防止の1秒間
    sleep(1)

    # JavaScriptのalertが実行されていると、それを消す作業が必要(しないと、driver.page_sourceでエラーが出る)
    while True:
        try:
            t = Alert(driver).text
            Alert(driver).dismiss()
            page.alert_txt.append(t)  # アラート内容を保存
            sleep(0.5)
        except NoAlertPresentException:
            break
        except Exception as e:
            return ["getAlertError_browser", page.url + "\n" + str(e)]

    # ブラウザから、現在開いているURLとそのHTMLを取得
    try:
        page.url = driver.current_url    # リダイレクトで違うURLの情報を取っている可能性があるため
        page.html = driver.page_source   # htmlソースを更新
    except Exception as e:
        return ['infoGetError_browser', page.url + '\n' + str(e)]
    else:
        page.hostName = urlparse(page.url).netloc   # ホスト名を更新
        page.scheme = urlparse(page.url).scheme     # スキームも更新
        if page.html:
            return re   # True or 'timeout'がreに入っている。タイムアウトでもhtmlは取れている.全ファイルのロードができてないだけ？
        else:
            return ['infoGetError_browser', page.url + '\n']


# watcher と ベースのタブ(ウェブページを読み込むために作成するabout:blank)以外のタブまたはウィンドウが開いていると、そのURLをリストで返す
def get_window_url(driver, watcher_id, base_id):
    url_list = list()
    try:
        windows = driver.window_handles
        for window in windows:
            if (window == watcher_id) or (window == base_id):
                continue
            driver.switch_to.window(window)
            url_list.append(driver.current_url)
            driver.close()
        driver.switch_to.window(watcher_id)
    except Exception as e:
        print(location() + str(e))
        raise
    return url_list


def take_screenshots(path, driver):
    try:
        img_name = str(len(os.listdir(path)))
        driver.save_screenshot(path + '/' + img_name + '.png')
    except Exception as e:
        print(location() + str(e))
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
            message = log_message['message']       # log_messageのkeyは "message" と "webview" (webviewの中身は謎の英数字)
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

    # # 今保存したURLの中で、同じサーバ内のURLはまるまる保存、それ以外はホスト名だけ保存
    # for url in page.request_url:
    #     url_domain = urlparse(url).netloc
    #     if page.hostName == url_domain:  # 同じホスト名(サーバ)のURLはそのまま保存
    #         page.request_url_same_server.append(url)
    #     if url_domain.count('.') > 2:  # xx.ac.jpのように「.」が2つしかないものはそのまま
    #         url_domain = '.'.join(url_domain.split('.')[1:])  # www.ritsumei.ac.jpは、ritsumei.ac.jpにする
    #     page.request_url_host.append(url_domain)  # ホスト名(ネットワーク部)だけ保存

"""
"""

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