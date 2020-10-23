from time import sleep
import csv
import os

from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.webdriver import WebDriver
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
from typing import Union, Dict, Any, cast, List
from webpage import Page
from logging import getLogger

logger = getLogger(__name__)

def stop_watcher_and_get_data(driver: WebDriver, wait: WebDriverWait, watcher_window: Union[str, int], page: Page) -> bool:
    """
    Watcher.htmlのStop Watchingボタンをクリック。
    拡張機能が監視を終え、収集したデータを記録。
    """
    logger.debug("Watcher: stop")
    try:
        # watcher.htmlに移動してstopをクリック
        # クリックすると、Watcher.htmlのdivタグ(id="contents")の中に、収集したデータを記録する
        driver.switch_to.window(watcher_window)
        wait.until(expected_conditions.visibility_of_element_located((By.ID, "stop")))
        elm = driver.find_element_by_id("stop")
        elm.click()

        # contentsの最後の要素がDOMに現れるまで待つ
        wait.until(expected_conditions.presence_of_element_located((By.ID, "EndOfData")))

        # watcher.htmlのHTMLをpageインスタンスのプロパティに保存
        page.watcher_html = driver.page_source # type: ignore

        # clearContentsをクリック
        elm: Any = driver.find_element_by_id("clearContents")
        elm.click()
        # 最後の要素が消えるまで待つ
        wait.until(expected_conditions.invisibility_of_element_located((By.ID, "EndOfData")))
    except Exception as err:
        logger.exception(f'{err}')
        return False
    else:
        logger.debug("Watcher: Get data from Watcher")
        return True


def start_watcher_and_move_blank(driver: WebDriver, wait: WebDriverWait, watcher_window: Union[int, str], blank_window: str) -> bool:
    """
    watcher.htmlのStart Watchingボタンをクリック。拡張機能が監視を始める
    """
    logger.debug("Watcher: starting...")
    try:
        driver.switch_to.window(watcher_window)
        wait.until(expected_conditions.visibility_of_element_located((By.ID, "start")))
        elm: Any = driver.find_element_by_id("start")
        elm.click()
        driver.switch_to.window(blank_window)
        wait.until(lambda d: "Watcher" != driver.title) # type: ignore
    except Exception as err:
        logger.exception(f'{err}')
        return False
    else:
        logger.debug("Watcher: started!")
        return True


def create_blank_window(driver: WebDriver, wait: WebDriverWait, watcher_window: Union[str, int]) -> Union[bool, str]:
    """
    ページを読み込むためのabout:blankのページを作る。
    blankページとwatcherページ以外は閉じる
    blankページが作れなければFalse
    """
    blank_window = False
    try:
        driver.switch_to.window(watcher_window)
        wait.until(expected_conditions.visibility_of_element_located((By.ID, "createBlankTab")))
        elm: Any = driver.find_element_by_id("createBlankTab")
        elm.click()
        for _ in range(30):
            windows: list[str] = driver.window_handles # type: ignore
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
    except Exception as err:
        logger.exception(f'{err}')
        return False
    else:
        return blank_window


def get_watcher_window(driver: WebDriver, wait: WebDriverWait) -> Union[bool, int, str]:
    """
    driverを取得した直後に呼ぶ
    """
    watcher_window = False
    logger.debug("Try to access extension page")
    try:
        wait.until(expected_conditions.visibility_of_all_elements_located((By.ID, "button")))
        wait.until(expected_conditions.presence_of_element_located((By.ID, "DoneAttachJS")))
    except TimeoutException as err:
        logger.exception(f"fail to access extension page by timeout: {err}")
        return False
    except Exception as err:
        logger.exception(f'fail to access extension page: {err}')
        return False
    try:
        windows: list[Union[int, str]] = driver.window_handles # type: ignore
        for window in windows:
            driver.switch_to.window(window)
            title = driver.title # type: ignore
            if title == "Watcher":
                watcher_window = window
            else:
                logger.debug("Fail to access Watcher extension, closing...")
                driver.close()
    except Exception as err:
        # 最悪、エラーが起きてもwatcher_windowがわかればよい
        logger.exception(f'Fail to open extension: {err}')

    try:
        driver.switch_to.window(watcher_window)
    except Exception as err:
        logger.exception(f"Faild to switch to extension page: {err}")
        return False
    else:
        return watcher_window

def get_fox_driver(screenshots: bool=False, user_agent: str='', org_path: str='') -> Union[bool, Dict[str, Any]]:
    """
    Firefoxを使うためのdriverをヘッドレスモードで起動
    ファイルダウンロード可能
    RequestURLの取得可能(アドオンを用いて)
    ログコンソールの取得不可能(アドオンの結果は</body>と</html>の間にはさむことで、取得する)
    """
    logger.debug("Setting FireFox driver...")
    # headless FireFoxの設定
    options: FirefoxOptions = FirefoxOptions()
    fpro: FirefoxProfile = FirefoxProfile()

    # ヘッドレスモードに
    options.add_argument('-headless')

    # user agent
    if user_agent:
        fpro.set_preference('general.useragent.override', user_agent)

    # アドオン使えるように
    try:
        src_dir = os.path.dirname(os.path.abspath(__file__))  # このファイル位置の絶対パスで取得 「*/src」
        extension_dir = src_dir + '/extensions'
        fpro.add_extension(extension=extension_dir + '/CrawlerExtension.xpi')
    except Exception as err:
        logger.exception(f'Failed to add_extension: {err}')

    # ファイルダウンロードできるように
    if org_path:
        fpro.set_preference('browser.download.folderList', 2)
        # 0:デスクトップ
        # 1:Downloadフォルダ
        # 2:ユーザ定義フォルダ
        fpro.set_preference('browser.download.dir', org_path + '/result/Download')
        # なければ作られる
    else:
        fpro.set_preference('browser.download.folderList', 0)
    # ダウンロードマネージャ起動しないように
    fpro.set_preference('browser.download.manager.showWhenStarting', False)
    fpro.set_preference('browser.helpApps.alwaysAsk.force', False)
    fpro.set_preference('browser.download.manager.alertOnEXEOpen', False)
    fpro.set_preference('browser.download.manager.closeWhenDone', True)
    # ダウンロード可能なMimeタイプの設定
    mime_list: list[str] = list()
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
        except csv.Error as err:
            logger.exception(f'{err}')
    fpro.set_preference('browser.helperApps.neverAsk.saveToDisk', ','.join(mime_list))

    # コンソールログを取得するために必要(ffではすべてのログが見れない)
    # d = DesiredCapabilities.FIREFOX
    # d['loggingPrefs'] = {'browser': 'ALL', 'driver': 'ALL', 'client': 'ALL', 'performance': 'ALL', 'server': 'ALL'}

    # Firefoxのドライバを取得。ここでフリーズしていることがあったため、スレッド化した
    # Todo: メモリが足りなかったらドライバーの取得でフリーズする
    try:
        t = GetFirefoxDriverThread(options=options, ffprofile=fpro)
        t.daemon = True
        t.start()
        t.join(10)
    except Exception as err:
        # runtime error とか
        logger.exception(f'Faild to get Firefox Driver Thread, retrying: {err}')
        sleep(10)
        try:
            t = GetFirefoxDriverThread(options=options, ffprofile=fpro)
            t.daemon = True
            t.start()
            t.join(10)
        except Exception:
            logger.exception(f'Faild to get Firefox Driver Thread again, Failed: {err}')
            return False

    if t.re is False:
        # ドライバ取得でフリーズしている場合
        if type(t.driver) == WebDriver:
            driver = cast(WebDriver, t.driver)
            quit_driver(driver) # 一応終了させて
        logger.info("Fail to getting driver: Freeze, return fail")
        return False
    if t.driver is False:
        # 単にエラーで取得できなかった場合
        logger.info("Fail to getting driver: Error, return fail")
        return False
    if type(t.driver) == WebDriver:
        driver = cast(WebDriver, t.driver)
        driver.set_window_size(1280, 1024)
    else:
        return False

    # 拡張機能のwindowIDを取得し、それ以外のwindowを閉じる
    # geckodriver 0.21.0 から HTTP/1.1 になった？ Keep-Aliveの設定が5秒のせいで、5秒間driverにコマンドがいかなかったらPipeが壊れる.
    # 0.20.1 にダウングレードするか、seleniumを最新にアップグレードすると、 Broken Pipe エラーは出なくなる。
    wait = WebDriverWait(driver, 5)
    watcher_window = get_watcher_window(driver, wait)
    if watcher_window is False:
        logger.warning("Fail to get watcher window, return fail")
        return False
    watcher_window = cast(Union[str, int], watcher_window)

    logger.debug("Setting FireFox driver... FIN!")
    return {"driver": driver, "wait": wait, "watcher_window": watcher_window}


def set_html(page: Page, driver: WebDriver) -> Union[bool, str, list[str]]:
    """
    ブラウザでURLにアクセス、HTMLを取得する
    """
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
        except Exception as err:
            logger.exception(f"Failed to get WebDriver thread error: {err}")
            return ['makingWebDriverGetThreadError', page.url + '\n' + str(err)]
    re = True
    if t.re is False:
        # Getスレッドがどこかでフリーズしている場合、t.reがFalseのまま
        re = 'timeout'
    elif t.re is not True:
        # TrueとFalse以外の場合、GET中にエラー発生
        exce: Union[bool, Exception] = t.re
        return ['Error_WebDriver', page.url + '\n' + str(exce)]

    # 読み込み、リダイレクト待機、連続アクセス防止の1秒間
    sleep(1)

    # JavaScriptのalertが実行されていると、それを消す作業が必要(しないと、driver.page_sourceでエラーが出る)
    while True:
        try:
            text: str = Alert(driver).text
            Alert(driver).dismiss()
            # アラート内容を保存
            page.alert_txt.append(text)
            sleep(0.5)
        except NoAlertPresentException:
            break
        except Exception as err:
            logger.exception(f"get Alert from browser: {err}")
            return ["getAlertError_browser", page.url + "\n" + str(err)]

    # ブラウザから、現在開いているURLとそのHTMLを取得
    try:
        page.url = cast(str, driver.current_url)    # リダイレクトで違うURLの情報を取っている可能性があるため
        page.html = cast(str, driver.page_source)   # htmlソースを更新
    except Exception as err:
        logger.exception("Failed to get info from Browser: {err}")
        return ['infoGetError_browser', page.url + '\n' + str(err)] # type: ignore
    else:
        page.hostName = urlparse(page.url).netloc   # ホスト名を更新
        page.scheme = urlparse(page.url).scheme     # スキームも更新
        if page.html:
            logger.debug("Correct to get html from page(%s)", page.url)
            # True or 'timeout'がreに入っている。タイムアウトでもhtmlは取れている.全ファイルのロードができてないだけ？
            return re
        else:
            logger.warning("Info get Error from browser: %s", page.url)
            return ['infoGetError_browser', page.url + '\n'] # type: ignore


def get_window_url(driver: WebDriver, watcher_id: Union[int, str], base_id: str) -> List[str]:
    """
    watcher と ベースのタブ以外のタブまたはウィンドウが開いていると、
    そのURLをリストで返す
    """
    url_list: list[str] = list()
    try:
        windows: list[str] = driver.window_handles # type: ignore
        for window in windows:
            if (window == watcher_id) or (window == base_id):
                continue
            driver.switch_to.window(window)
            url_list.append(cast(str, driver.current_url))
            driver.close()
        logger.warning("get other url, switch to watcher page...")
        driver.switch_to.window(watcher_id)
    except Exception as err:
        logger.exception(f'{err}')
        raise
    return url_list


def take_screenshots(path: str, driver: WebDriver) -> bool:
    """
    スクリーンショットを撮影する
    成功したら True, 失敗したら False
    """
    try:
        img_name = str(len(os.listdir(path)))
        driver.save_screenshot(path + '/' + img_name + '.png')
    except Exception as err:
        logger.exception(f'Failed to take screenshot: {err}')
    else:
        return True

    return False


def quit_driver(driver: WebDriver) -> bool:
    """
    WebDriverを終了させる
    """
    try:
        driver.quit()
    except Exception as err:
        logger.exception(f'Failed to quit driver: {err}')
        return False
    else:
        logger.debug("Quit WebDriver")
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