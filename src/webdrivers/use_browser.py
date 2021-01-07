from __future__ import annotations

import os
from logging import getLogger
from multiprocessing import Queue
from time import sleep
from typing import Any, Union, cast
from urllib.parse import urlparse
from dealwebpage.fix_urls import complete_url_by_html

from dealwebpage.html_read_thread import WebDriverGetThread
from dealwebpage.webpage import Page
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from utils.logger import worker_configurer

logger = getLogger(__name__)

def configure_logger(queue_log: Queue[Any]):
    """
    Loggerをセット
    """
    worker_configurer(queue_log, logger)

def create_blank_window(driver: WebDriver, wait: WebDriverWait, watcher_window: Union[str, int]) -> Union[bool, str]:
    """
    ページを読み込むためのabout:blankのページを作る。
    blankページとwatcherページ以外は閉じる
    blankページが作れなければFalse
    """
    blank_window = False
    logger.debug("create blank window")
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

GET_WEBDRIVER_RETRY = 2

def set_html(page: Page, driver: WebDriver) -> Union[bool, str, list[str]]:
    """
    ブラウザでURLにアクセス、HTMLを取得する
    """
    logger.info("call set_html")
    for i in range(0, GET_WEBDRIVER_RETRY):
        try:
            # URLに接続する(フリーズすることがあるので、スレッドで行う)
            t = WebDriverGetThread(driver, page.url)
            t.start()
            t.join(timeout=20)   # 60秒のロード待機時間
            # timeout してもそのまま処理を続行する
            # 以降の処理でうまくHTMLが出てる場合は調査するしだめならだめで処理する
            # if t.is_alive():
            #     raise TimeoutException("Failed to get WebDriverGetThread")
        except Exception as err:
            if i < GET_WEBDRIVER_RETRY - 1:
                logger.info(f"Failed to access {page.url}: {err}")
                driver.close()
                # スレッド生成時に run timeエラーが出たら、10秒待ってもう一度
                sleep(10)
            else:
                logger.error(f"Failed to get WebDriver thread error: {err}")
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
            logger.warning(f'get Alert from browser: {err}')
            return ["getAlertError_browser", page.url + "\n" + str(err)]

    # ブラウザから、現在開いているURLとそのHTMLを取得
    try:
        page.url = cast(str, driver.current_url)    # リダイレクトで違うURLの情報を取っている可能性があるため
        page.html = cast(str, driver.page_source)   # htmlソースを更新
    except Exception as err:
        logger.exception(f"Failed to get info from Browser: {err}")
        return ['infoGetError_browser', page.url + '\n' + str(err)] # type: ignore
    else:
        # iframeの先のHTMLたちを結合する
        # TODO: まじでそのまま後ろにつなげているだけなので許してほしい
        iframe_list = driver.find_elements_by_tag_name("iframe")
        for iframe in iframe_list:
            try:
                iframe_url = iframe.get_property("src")
                driver.switch_to.frame(iframe)
                print(iframe_url)
                iframe_html = complete_url_by_html(driver.page_source, iframe_url, page.html_special_char)
                print(iframe_html)
                # iframe内のURLを修正する
                page.html += iframe_html
                # 高速に入れ替えすぎると要素の取得が追い付かないため
            except:
                logger.info("Failed to switch iframe")
                pass
            sleep(0.1)
        driver.switch_to.default_content()
        page.hostName = urlparse(page.url).netloc   # ホスト名を更新
        page.scheme = urlparse(page.url).scheme     # スキームも更新
        if page.html:
            logger.debug("Correct to get html from page(%s)", page.url)
            # True or 'timeout'がreに入っている。タイムアウトでもhtmlは取れている.全ファイルのロードができてないだけ？
            return re
        else:
            logger.warning("Info get Error from browser: %s", page.url)
            return ['infoGetError_browser', page.url + '\n'] # type: ignore


def get_window_url(driver: WebDriver, watcher_id: Union[int, str], base_id: str) -> set[str]:
    """
    watcher と ベースのタブ以外のタブまたはウィンドウが開いていると、
    そのURLをリストで返す
    """
    url_list: set[str] = set()
    try:
        windows: set[str] = driver.window_handles # type: ignore
        for window in windows:
            if (window == watcher_id) or (window == base_id):
                continue
            driver.switch_to.window(window)
            url_list.add(cast(str, driver.current_url))
            driver.close()
        logger.debug("get other url, switch to watcher page... %s", str(watcher_id))
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
    logger.debug("Call quit_driver func")
    try:
        driver.close()
    except Exception as err:
        logger.info(f"There are no window.... {err}")
        pass

    logger.debug("Try to quit_driver")
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
