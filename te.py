import dbm
import time
import os
import json
import use_web_driver
import webpage
from collections import deque
import socket
from urllib.parse import urlparse
from file_rw import r_file

dic = dict()
iframe_url = set()


def fun(i):
    print(i, 'start')
    if 'tfidf' not in i:
        return 0
    with open('../' + i, 'r') as f:
        content = f.read()
    s = content
    tfidf_json = list()
    while True:
        if s.find(')') == -1:
            break
        if s.find(',') == -1:
            break
        tfidf = s[s.find(',') + 2: s.find(')')]
        s = s[s.find(')'):]
        s = s[s.find('('):]
        try:
            tfidf_json.append(float(tfidf))
        except Exception as e:
            print(e, tfidf)
    import json
    with open('../' + i + '.json', 'w') as f:
        json.dump(tfidf_json, f)
    print(i, 'end')


def tt():

    global iframe_url
    obj = 'iframe'
    url_set = {'abc', 'ddf', 'eeff'}
    print(iframe_url)
    exec(obj + "_url.update(url_set)")
    print(iframe_url)
    import json
    with open('tttt.json', 'w') as f:
        exec("json.dump(list(" + obj + "_url), f)")


if __name__ == '__main__':
    tt()

    # from use_web_driver import driver_get, set_html, set_request_url
    # from webpage import Page
    # from bs4 import BeautifulSoup
    # driver = driver_get(False)
    # url = 'http://192.168.0.232/home/redirect_start.html'
    # page = Page(url, 'test')


    # urlopenとphantomjsそれぞれでJSによるリンク生成に対応できているかのテスト
    """urlopen_result = page.set_html_and_content_type_urlopen(page.url, time_out=60)
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
    """
