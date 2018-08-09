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


if __name__ == '__main__':
    """
    from operate_main import kill_chrome, kill_family
    kill_chrome(process='chrome')

    """

    from use_web_driver_chrome import driver_get, set_html, quit_driver
    from webpage import Page
    from bs4 import BeautifulSoup

    user_agent = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko)'
    driver = driver_get(False, user_agent=user_agent)

    url_kouchi = 'http://falsification.cysec.cs.ritsumei.ac.jp/home/whatsnew/20131219kouchi'
    url = 'http://www.ritsumei.ac.jp/tanq/352217/'
    url = 'file:///home/hiro/Desktop/falsification/test_site/home/whatsnew/20131219kouchi'
    url = 'file:///home/hiro/Desktop/falsification/mal_site/mal_top.html'
    url_autodl = 'http://falsification.cysec.cs.ritsumei.ac.jp/home/members'

    page = Page(url_autodl, 'test')
    re = set_html(page, driver)
    print(page.html)
    # driver.find_element_by_id('dLoad2').click()
    for i in range(50):
        time.sleep(1)
        print('{i}, '.format(i=i+1), end='', flush=True)
    print(driver.current_url)
    quit_driver(driver)


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
