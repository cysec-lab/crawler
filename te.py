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
    url = 'http://falsification.cysec.cs.ritsumei.ac.jp/home/aceess'
    host_name = urlparse(url).netloc
    print(host_name)

    # Pageオブジェクトを作成
    page = Page(url, 'tes')

    # urlopenで接続
    urlopen_result = page.set_html_and_content_type_urlopen(page.url, time_out=60)
    print(page.url)

    redirect = check_redirect(page, host_name)
    print(redirect)

    from use_web_driver import driver_get, set_html
    driver = driver_get(False)
    phantom_result = set_html(page=page, driver=driver)
    print(page.url)
    redirect = check_redirect(page, host_name)
    print(redirect)

    from file_rw import r_file
    data_temp = r_file('ROD/LIST/REDIRECT_LIST.txt')
    after_redirect_list = data_temp.split('\n')
    if '' in after_redirect_list:
        after_redirect_list.remove('')
    redirect_host = urlparse(page.url).netloc
    if not [white for white in after_redirect_list if redirect_host.endswith(white)]:
        print('alert')
    else:
        print('no alert')
