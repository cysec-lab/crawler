import os
import json


def get_hash():
    os.chdir('../url_hash_json2')
    host = os.listdir()
    """
    for i in host:
        with open(i, 'r') as f:
            url_dic = json.load(f)
        del_list = []
        for k, v in url_dic.items():
            if len(v) == 4:
                if len(v[3]) == 0:
                    print(v)
        if del_list:
            for k in del_list:
                del url_dic[k]
            with open(i, 'w') as f:
                json.dump(url_dic, f)
    """
    for i in host:
        with open(i, 'r') as f:
            url_dic = json.load(f)
        del_list = []
        for k, v in url_dic.items():
            if len(v) == 64:
                print(v)

if __name__ == '__main__':
    get_hash()
