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
    print("URL is :{}".format(page.url))
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

    if page.download_info:
        for i, v in page.download_info.items():
            print(v)
    if page.among_url:
        for i in page.among_url:
            print(i)
    print("URL is :{}".format(page.url))
    print(page.html)

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

    url = "http://falsification.cysec.cs.ritsumei.ac.jp/home/redirect_start.html"
    url = "http://www.ritsumei.ac.jp/file.jsp?id=388532"

    p1 = Process(target=fun, args=('1', url,))
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


def import_file(path):             # 実行でディレクトリは「crawler」
    setting_dict_dict = dict()
    settings_list = ["DOMAIN", "WHITE", "IPAddress", "REDIRECT", "BLACK"]
    for setting in settings_list:
        if os.path.exists("{}/{}.json".format(path, setting)):
            with open("{}/{}.json".format(path, setting), "r") as f:
                setting_dict_dict[setting] = json.load(f)
        else:
            setting_dict_dict[setting] = dict()
    for i, v in setting_dict_dict.items():
        print(i, v)
    return setting_dict_dict


if __name__ == '__main__':
    # main()
    from threading import active_count
    from check_allow_url import check_searched_url, CheckSearchedIPAddressThread
    filtering_dict = import_file("../organization/ritsumeikan/ROD/LIST")
    url_tuple = ("http://www.ritsuei.ac.jp/top", "START")
    s = list()

    print(active_count())
    res = check_searched_url(url_tuple, int(time.time()), filtering_dict)
    s.append(res)
    print(id(res))

    url_tuple = ("http://www.ritsumei.ac.jp/top", "START")
    res = check_searched_url(url_tuple, int(time.time()), filtering_dict)
    print(id(res))
    s.append(res)
    print(active_count())
    print(type(res))

    for res in s:
        print(res)
        if type(res) == CheckSearchedIPAddressThread:
            time.sleep(2)
            print(active_count())
            res.lock.release()
            time.sleep(1)
            print(active_count())
            print(res.result)
