import shutil
import os
import json


def del_falsification_RAD():
    if os.path.exists('RAD/df_dict/falsification-cysec-cs-ritsumei-ac-jp.json'):
        os.remove('RAD/df_dict/falsification-cysec-cs-ritsumei-ac-jp.json')
    if os.path.exists('RAD/tag_data/falsification-cysec-cs-ritsumei-ac-jp.json'):
        os.remove('RAD/tag_data/falsification-cysec-cs-ritsumei-ac-jp.json')
    if os.path.exists('RAD/url_hash_json/falsification-cysec-cs-ritsumei-ac-jp.json'):
        os.remove('RAD/url_hash_json/falsification-cysec-cs-ritsumei-ac-jp.json')
    if os.path.exists('RAD/temp/progress_falsification-cysec-cs-ritsumei-ac-jp.pickle'):
        os.remove('RAD/temp/progress_falsification-cysec-cs-ritsumei-ac-jp.pickle')


def copy_ROD_from_cysec():

    # 頻出単語、idf辞書はそのままコピー
    src_path = 'ROD/frequent_word_100/www-cysec-cs-ritsumei-ac-jp.json'
    if os.path.exists(src_path):
        shutil.copyfile(src_path, 'ROD/frequent_word_100/falsification-cysec-cs-ritsumei-ac-jp.json')

    src_path = 'ROD/idf_dict/www-cysec-cs-ritsumei-ac-jp.json'
    if os.path.exists(src_path):
        shutil.copyfile(src_path, 'ROD/idf_dict/falsification-cysec-cs-ritsumei-ac-jp.json')

    # tag_dataとurl_hash_jsonはkeyのURL部分を変更してコピー
    src_path = 'ROD/tag_data/www-cysec-cs-ritsumei-ac-jp.json'
    if os.path.exists(src_path):
        # readして書き換え
        with open(src_path, mode='r') as f:
            tag_data_dict = json.load(f)
        falsification_tag_dict = dict()
        for i, v in tag_data_dict.items():
            key = i.replace('www.cysec.cs.ritsumei.ac.jp', 'falsification.cysec.cs.ritsumei.ac.jp')
            falsification_tag_dict[key] = v
        # 保存
        with open('ROD/tag_data/falsification-cysec-cs-ritsumei-ac-jp.json', mode='w') as f:
            json.dump(falsification_tag_dict, f)

    src_path = 'ROD/url_hash_json/www-cysec-cs-ritsumei-ac-jp.json'
    if os.path.exists(src_path):
        # readして書き換え
        with open(src_path, mode='r') as f:
            url_hash_dict = json.load(f)
        falsification_hash_dict = dict()
        for i, v in url_hash_dict.items():
            key = i.replace('www.cysec.cs.ritsumei.ac.jp', 'falsification.cysec.cs.ritsumei.ac.jp')
            falsification_hash_dict[key] = v
        # 保存
        with open('ROD/url_hash_json/falsification-cysec-cs-ritsumei-ac-jp.json', mode='w') as f:
            json.dump(falsification_hash_dict, f)
