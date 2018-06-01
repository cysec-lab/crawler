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


def return_children(my_pid):
    try:
        children = subprocess.check_output(['ps', '--ppid', str(my_pid), '--no-heading', '-o', 'pid'])
    except subprocess.CalledProcessError:
        print('Non children')
        return list()
    else:
        print('me : ', my_pid)
        child_list = children.decode().replace(' ', '').split('\n')
        try:
            child_list.remove('')
        except ValueError:
            pass
        return child_list


if __name__ == '__main__':

    import sys
    import subprocess

    # meより下の家族プロセスkillする
    me = os.getpid()
    me = 11943
    family = return_children(me)
    print(family)
    i = 0
    while True:
        pid_ = family[i]
        family.extend(return_children(pid_))
        print(family)
        i += 1
        if len(family) == i:
            break
    for kill_pid in family:
        os.system("kill " + kill_pid)



    # from use_web_driver import driver_get, set_html
    # from webpage import Page
    # from bs4 import BeautifulSoup
    # driver = driver_get(False)
    # url = 'http://falsification.cysec.cs.ritsumei.ac.jp/home/research'
    # page = Page(url, 'test')
    #
    # urlopen_result = page.set_html_and_content_type_urlopen(page.url, time_out=60)
    # soup = BeautifulSoup(page.html, 'lxml')
    # print(soup.prettify())
    #
    # print('------------------------')
    # phantom_result = set_html(page=page, driver=driver)
    # soup = BeautifulSoup(page.html, 'lxml')
    # print(soup.prettify())

    # import os
    # from multiprocessing import Pool
    # lis = os.listdir('..')
    # print(lis)
    # p = Pool(8)
    #
    # p.map(fun, lis)

    # import matplotlib.pyplot as plt
    # lis = os.listdir('..')
    # print(lis)
    # plt.style.use('ggplot')
    # fig = plt.figure()
    # ax = fig.add_subplot(1, 1, 1)
    #
    # for i in lis:
    #     if i.endswith('.json'):
    #         with open('../' + i, 'r') as f:
    #             json_file = json.load(f)
    #     else:
    #         continue
    #     M = max(json_file)
    #
    #     print(len(json_file))
    #     y = [round(tmp, 4) for tmp in json_file if round(tmp, 4) < 0.05]
    #     print(len(y))
    #     x = range(len(y))
    #
    #     # 折れ線グラフの用意
    #     ax.scatter(x, y, label="y points")
    #
    #     # タイトルを用意
    #     ax.set_title("Title")
    #     ax.set_ylabel("Y1 and Y2")
    #     ax.set_xlabel("X")
    #
    #     # 凡例を付ける
    #     ax.legend()
    #
    #     # グラフを描く
    #     plt.show()
    #
    #     break
