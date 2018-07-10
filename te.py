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
    from use_web_driver import driver_get, set_html, set_request_url
    from webpage import Page
    from bs4 import BeautifulSoup
    driver = driver_get(False)
    url = 'http://falsification.cysec.cs.ritsumei.ac.jp/home/papers'
    page = Page(url, 'test')

    # 重要単語のテスト
    from mecab import get_tf_dict_by_mecab, add_word_dic, make_tfidf_dict, get_top10_tfidf
    from urldict import UrlDict
    f_name = 'falsification-cysec-cs-ritsumei-ac-jp'
    urlDict = UrlDict(f_name)
    urlDict.load_url_dict(path='../organization/ritsumeikan/ROD/url_hash_json/')
    print(urlDict.url_dict[url])
    path = '../organization/ritsumeikan/ROD/idf_dict/' + f_name + '.json'
    if os.path.exists(path):
        if os.path.getsize(path) > 0:
            with open(path, 'r') as f:
                word_idf_dict = json.load(f)

    phantom_result = set_html(page=page, driver=driver)
    soup = BeautifulSoup(page.html, 'lxml')
    hack_level, word_tf_dict = get_tf_dict_by_mecab(soup)
    print(word_tf_dict)
    if word_tf_dict is not False:
        word_tfidf = make_tfidf_dict(idf_dict=word_idf_dict, tf_dict=word_tf_dict)  # tf-idf値を計算
        top10 = get_top10_tfidf(tfidf_dict=word_tfidf, nth='6')  # top10を取得。ページ内に単語がなかった場合は空リストが返る
        # ハッシュ値が異なるため、重要単語を比較
        pre_top10 = urlDict.get_top10_from_url_dict(url=page.url)  # 前回のtop10を取得
        top10 = ['ため', 'hacked']
        print(top10)
        print(pre_top10)
        if pre_top10 is not None:
            symmetric_difference = set(top10) ^ set(pre_top10)  # 排他的論理和
            print(symmetric_difference)
            if len(symmetric_difference) > ((len(top10) + len(pre_top10)) * 0.8):
                print(((len(top10) + len(pre_top10)) * 0.8))
                print('changed')
            else:
                print('変わらず')
    """

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
