from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from urllib.parse import urlparse
from copy import deepcopy
from content_get import PhantomGetThread, DriverGetThread
import signal


# phantomJSを使うためのdriverを返す
def driver_get(screenshots):
    # PhantomJSの設定
    des_cap = dict(DesiredCapabilities.PHANTOMJS)
    des_cap["phantomjs.page.settings.userAgent"] = (
        'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    )
    if not screenshots:
        des_cap["phantomjs.page.settings.loadImages"] = False
    des_cap['phantomjs.page.settings.resourceTimeout'] = 60   # たぶん意味ない

    # PhantomJSのドライバを取得。ここでフリーズしていることがあったため、スレッド化した
    try:
        t = DriverGetThread(des_cap)
        t.start()
        t.join(10)
    except Exception:
        sleep(10)
        try:
            t = DriverGetThread(des_cap)
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


# pageオブジェクトのプロパティに値を格納していく
# エラーがでたらそれを返す
def set_html(page, driver):
    try:
        t = PhantomGetThread(driver, page.url)
        t.start()
        t.join(timeout=60)   # 60秒のロード待機時間
    except Exception:
        # スレッド生成時に run timeエラーが出たら、10秒待ってもう一度
        sleep(10)
        try:
            t = PhantomGetThread(driver, page.url)
            t.start()
            t.join(timeout=60)  # 60秒のロード待機時間
        except Exception as e:
            return ['makeThreadError_phantom', page.url + '\n' + str(e)]

    re = True
    if t.re is False:
        re = 'timeout'
    elif t.re is not True:
        return ['Error_phantom', page.url + '\n' + str(t.re)]

    # 読み込み、リダイレクト待機、連続アクセス防止の1秒間
    # sleep(1)
    current_url = driver.current_url
    relay_url = list()
    for i in range(10):
        if current_url != driver.current_url:     # 0.1秒ごとにURLを監視
            current_url = driver.current_url
            relay_url.append(current_url)
        sleep(0.1)
    if set(relay_url).difference(driver.current_url):   # 最後のURL以外に中継URLがあれば、保存
        page.relay_url = deepcopy(relay_url)

    try:
        wait = WebDriverWait(driver, 5)
        wait.until(expected_conditions.presence_of_all_elements_located)   # ロード完了まで最大5秒待つ(たぶんロードは完了しているのでいらない)
        # SSL認証で失敗するとabout:blankになる
        # SSL認証で失敗していないのにabout:blankは5秒待つ
        log_content = driver.get_log('har')[0]['message']
        if driver.current_url == 'about:blank':
            if '"statusText":"(ssl failure)"' not in log_content:
                sleep(5)
        page.url = driver.current_url    # リダイレクトで違うURLの情報を取っている可能性があるため
        page.html = driver.page_source   # htmlソースを更新
    except Exception as e:
        return ['infoGetError_phantom', page.url + '\n' + str(e)]
    else:
        page.hostName = urlparse(page.url).netloc   # ホスト名を更新
        page.scheme = urlparse(page.url).scheme     # スキームも更新
        if page.html:
            return re   # True or 'timeout'がreに入っている。タイムアウトでもhtmlは取れている場合がある.全ファイルのロードができてないだけ？
        else:
            return ['infoGetError_phantom', page.url + '\n']


def set_request_url(page, driver):
    try:
        log_content = driver.get_log('har')[0]['message']
    except:
        raise
    temp = set()   # ページをロードするのにリクエストしたurlを入れる集合
    re = list()    # GETとPOST以外のメソッドがあれば入る
    # GETとPOSTのメソッドのURLをpageの属性に保存
    log_content2 = log_content
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

    # temp2はログの中に出てきたURLを全て取り出す
    # temp2 = set()
    # while True:
    #     get = log_content2.find('"http')
    #     if get == -1:
    #         break
    #     if '://' in log_content2[get: get+9]:
    #         end = log_content2[get + 1:].find('"')
    #         url_2 = log_content2[get+1: get + 1 + end]
    #         temp2.add(url_2)
    #     else:
    #         end = get + 3
    #     log_content2 = log_content2[end:]

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
        driver.service.process.send_signal(signal.SIGTERM)
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