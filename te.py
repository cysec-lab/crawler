import time
import sys
import os
import json
import webpage
from collections import deque
from urllib.parse import urlparse
from multiprocessing import Process
from use_browser import get_fox_driver, set_html, quit_driver, create_blank_window, start_watcher_and_move_blank
from use_browser import stop_watcher_and_get_data
from webpage import Page
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from location import location


def fun(num, url_2):
    # fo = None
    # fo = open("/home/cysec/Desktop/log_" + num + ".txt", "a")
    # sys.stdout = fo

    user_agent = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko)'

    # 以下、初期設定
    print("Get WebDriver")
    s = time.time()
    driver_info = get_fox_driver(False, user_agent=user_agent)
    print(driver_info)
    driver = driver_info["driver"]
    watcher_window = driver_info["watcher_window"]
    wait = driver_info["wait"]
    print("initialize time = {}".format(time.time() - s))

    driver.delete_all_cookies()

    # 毎度、接続する前にする
    print("Create Blank Tab")
    s = time.time()
    blank_window = create_blank_window(driver=driver, wait=wait, watcher_window=watcher_window)
    print("watcher :{} , blank :{}".format(watcher_window, blank_window))
    print("create blank time = {}".format(time.time() - s))

    print("Start watching and move blank page")
    s = time.time()
    start_watcher_and_move_blank(driver=driver, wait=wait, watcher_window=watcher_window, blank_window=blank_window)
    print("start watcher and move blank time = {}".format(time.time() - s))

    s = time.time()
    page = Page(url_2, 'test')
    print("Access to URL and Loading")
    re = set_html(page, driver)
    print("set_html time = {}".format(time.time() - s))

    print("Stop Watcher")
    s = time.time()
    stop_watcher_and_get_data(driver=driver, wait=wait, watcher_window=watcher_window, page=page)
    print("stop watcher time = {}".format(time.time() - s))

    s = time.time()
    soup = BeautifulSoup(page.watcher_html, 'lxml')
    page.extracting_extension_data(soup)
    print("extract data time = {}".format(time.time() - s))
    print(page.request_url)
    print(len(page.request_url))
    for i in page.request_url:
        if "from" in i:
            print(i)

    if page.download_info:
        for i, v in page.download_info.items():
            print(v)

    print("Quit driver")
    quit_driver(driver)


def main():
    # from operate_main import kill_chrome
    # kill_chrome(process='geckodriver')
    # return 0

    url = 'file:///home/hiro/Desktop/falsification/test_site/home/redirect_start.html'
    url = 'file:///home/hiro/Desktop/falsification/mal_site/mal_top.html'
    url_autodl = 'http://falsification.cysec.cs.ritsumei.ac.jp/home/members'
    url = 'file:///home/hiro/Desktop/falsification/test_site/home/whatsnew/20131219kouchi.html'
    url = 'http://www.ritsumei.ac.jp/'
    url_kouchi = 'http://falsification.cysec.cs.ritsumei.ac.jp/home/whatsnew/20131219kouchi'

    url = "http://www.slp.is.ritsumei.ac.jp/publications-jis.html"

    p1 = Process(target=fun, args=('1', url_autodl,))
    # p2 = Process(target=fun, args=('2', url,))
    p1.start()  # スタート
    # p2.start()  # スタート


def pp():
    import csv
    src_dir = os.path.dirname(os.path.abspath(__file__))  # このファイル位置の絶対パスで取得 「*/src」
    mime_list = list()
    mime_file_dir = src_dir + '/files/mime'
    for csv_file in os.listdir(mime_file_dir):
        try:
            with open(mime_file_dir + "/" + csv_file) as f:
                csv_reader = csv.DictReader(f)
                for row in csv_reader:
                    if row["Template"]:
                        mime_list.append(row["Template"])
        except csv.Error as e:
            print(location() + str(e), flush=True)
    for i in mime_list:
        if "application/vnd.openxmlformats-officedocument.wordprocessingml.document" == i:
            print(i)


if __name__ == '__main__':
    main()
    # pp()
    # driver.find_element_by_id('dLoad2').click()
    # for i in range(50):
    #     print(driver.current_url)
    #     time.sleep(1)
    #     print('{i}, '.format(i=i+1), end='', flush=True)

    # request_urls = set()
    # receive_urls = set()
    # i = 0
    # import json
    # performance_log = driver.get_log('driver')
    #
    # for log in performance_log:
        # print("{} \t {}".format(log['level'], log['message']))
        # # logのkeyは 'message' と "timestamp" のみ
        # log_message = json.loads(log['message'])
        # # log_messageのkeyは "message" と "webview" のみ(webviewの中身は謎のx16)
        # message = log_message['message']
        # print('{} \t {}'.format(message['method'], message['params']))
        # # messageのkeyは "params" と "method"
        # if message['method'] == 'Network.requestWillBeSent':
        #     u = message['params']['request']['url']
        #     request_urls.add(u)
        # elif message['method'] == 'Network.responseReceived':
        #     # print("RECEIVE \t {}".format(message['params']['response']))
        #     u = message['params']['response']['url']
        #     receive_urls.add(u)

    # print(len(request_urls))
    # print('request urls : {}'.format(request_urls))
    # print(len(receive_urls))
    # print('receive urls : {}'.format(receive_urls))


    # urlopenとphantomjsそれぞれでJSによるリンク生成に対応できているかのテスト
    """
    urlopen_result = page.set_html_and_content_type_urlopen(page.url, time_out=60)
    print(urlopen_result)
    soup = BeautifulSoup(page.html, 'lxml')
    #print(soup.prettify())
    st = str(soup.prettify())
    with open('urlopen.html', 'w', encoding='utf-8') as f:
        f.write(st)
    page.make_links_html(soup)
    url_open = page.links
    print(url_open)
    print('------------------------')
    phantom_result = set_html(page=page, driver=driver)
    soup = BeautifulSoup(page.html, 'lxml')
    #print(soup.prettify())
    st = str(soup.prettify())
    with open('phantom.html', 'w', encoding='utf-8') as f:
        f.write(st)
    page.make_links_html(soup)
    phantomjs = page.links
    print(phantomjs)
    re, temp2 = set_request_url(page, driver)
    print(re)
    print(temp2)
    print(len(temp2))
    print(len(page.request_url))
    print(temp2.difference(page.request_url))
    quit_driver(driver)
    """
