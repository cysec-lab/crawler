from selenium import webdriver
import selenium.common
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from os import path
from urllib.parse import urlparse
from copy import deepcopy
import phantom_get


# phantomJSを使うためのdriverを返す
def driver_get():
    des_cap = dict(DesiredCapabilities.PHANTOMJS)
    des_cap["phantomjs.page.settings.userAgent"] = (
        'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    )
    # des_cap["phantomjs.page.settings.loadImages"] = False
    des_cap['phantomjs.page.settings.resourceTimeout'] = 60   # たぶん意味ない
    try:
        driver = webdriver.PhantomJS(desired_capabilities=des_cap, service_log_path=path.devnull)
    except selenium.common.exceptions.WebDriverException:
        sleep(1)
        try:
            driver = webdriver.PhantomJS(desired_capabilities=des_cap, service_log_path=path.devnull)
        except selenium.common.exceptions.WebDriverException:
            print('End by WebDriverException.')
            return False
    # たぶん意味ない
    driver.set_page_load_timeout = 60  # ページを構成するファイルのロードのタイムアウト?
    driver.timeout = 30   # リクエストのタイムアウト?
    return driver


def set_html(page, driver):
    t = phantom_get.PhantomGetThread(driver, page.url)
    t.start()
    t.join(timeout=60)   # 60秒のロード待機時間
    re = True
    if t.re is False:
        re = 'timeout'
    elif t.re is not True:
        return ['Error_phantom', page.url + '\n' + str(t.re)]
    sleep(1)
    try:
        wait = WebDriverWait(driver, 5)
        wait.until(expected_conditions.presence_of_all_elements_located)   # ロード完了まで最大5秒待つ(たぶんロードは完了しているのでいらない)
        page.url = driver.current_url    # リダイレクトで違うURLの情報を取っている可能性があるため
        page.html = driver.page_source   # htmlソースを更新
    except Exception as e:
        return ['infoGetError_phantom', page.url + '\n' + str(e)]
    else:
        page.hostName = urlparse(page.url).netloc   # ホスト名を更新
        page.scheme = urlparse(page.url).scheme     # スキームも更新
        if page.html:
            return re   # True or 'timeout'がreに入っている。タイムアウトでもhtmlは取れている.全ファイルのロードができてないだけ？
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
        if url_domain.count('.') > 1:                   # xx.com　のような「.」が一つしかない場合がある
            url_domain = '.'.join(url_domain.split('.')[1:])
        page.request_url_host.append(url_domain)     # ホスト名だけ保存
    return re


def get_window_url(page, driver):
    url_list = list()
    try:
        windows = driver.window_handles
        for window in windows[1:]:
            driver.switch_to.window(window)
            url_list.append((driver.current_url, page.src, page.url, 'new_window_url'))
            driver.close()
        driver.switch_to.window(windows[0])
    except:
        raise
    return url_list

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