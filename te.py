import dbm
import time
import os
import json


if __name__ == '__main__':

    f = open('ROD/url_hash_json/www-apu-ac-jp.json', 'r')

    content = json.load(f)
    f.close()
    print(content['http://www.apu.ac.jp/careers/page/content0001.html/?&version='])

