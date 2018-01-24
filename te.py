import dbm
import time
import os
import json
import use_web_driver
import webpage
from collections import deque
import socket
from urllib.parse import urlparse

dic = dict()


def fun(tup):
    print(id(tup))
    dic[tup[0]] = tup




if __name__ == '__main__':

    from webpage import Page
    from crawler3 import check_redirect
    url = 'http://www.ritsumei.ac.jp/acd/re/k-rsc/kikou/2006/20060916ohshima.htm'
    url = 'https://sites.google.com/site/cidllaboratory/'
    host_name = urlparse(url).netloc

    # Pageオブジェクトを作成
    page = Page(url, 'tes')

    # urlopenで接続
    urlopen_result = page.set_html_and_content_type_urlopen(page.url, time_out=60)
    print(page.url)

    redirect = check_redirect(page, host_name)
    print(redirect)

    from use_web_driver import driver_get, set_html, quit_driver
    driver = driver_get(False)
    phantom_result = set_html(page=page, driver=driver)
    print(page.url)
    print(page.html)
    redirect = check_redirect(page, host_name)
    print(redirect)

    quit_driver(driver)
