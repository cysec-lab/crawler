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
    print(page.download_info)
    print(type(page.download_info["1"]["TotalBytes"]))
    print(type(page.download_info["1"]["FileSize"]))

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
    p1 = Process(target=fun, args=('1', url_autodl,))

    url = "https://www.amazon.co.jp/RAZER-RZ01-02330100-R3A1-Razer-Basilisk-%E6%9C%89%E7%B7%9A%E3%82%B2%E3%83%BC%E3%83%9F%E3%83%B3%E3%82%B0%E3%83%9E%E3%82%A6%E3%82%B9%E3%80%90%E6%97%A5%E6%9C%AC%E6%AD%A3%E8%A6%8F%E4%BB%A3%E7%90%86%E5%BA%97%E4%BF%9D%E8%A8%BC%E5%93%81%E3%80%91RZ01-02330100-R3A1/dp/B0779P36CZ?pf_rd_m=AN1VRQENFRJN5&pf_rd_p=34099e8e-4cbf-4001-b107-e3dc96868f55&pf_rd_r=165b99b3-dc0a-4b70-a343-c94686624398&pd_rd_wg=UhleS&pf_rd_s=desktop-gateway&pf_rd_t=40701&pd_rd_w=lsLz5&pf_rd_i=desktop-gateway&pd_rd_r=165b99b3-dc0a-4b70-a343-c94686624398&ref_=pd_gw_qpp"

    # p2 = Process(target=fun, args=('2', url,))
    # p3 = Process(target=fun, args=('3', url,))
    # url = "https://qiita.com/Shitimi_613/items/254730d6dff96f6459ca"
    # p4 = Process(target=fun, args=('4', url,))
    p1.start()  # スタート
    # p2.start()  # スタート
    # p3.start()
    # p4.start()


if __name__ == '__main__':
    main()

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
