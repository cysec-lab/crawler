import shutil
import os
import json

# サイバーセキュリティ研究室のサイトのクローリング結果(RODデータ)から、自作改ざんサイトの検出に使うデータ(RODデータ)を作成する
# 端的に言うと、ホスト名を変えているだけ。だった気がする

# RADに自作改ざんサイトの結果が残っていると、それを含めたデータが作成されてしまう(次回以降のクローリングに影響が出てしまう)ため、削除する
def del_falsification_RAD(org_path):
    if os.path.exists(org_path + '/RAD/df_dict/falsification-cysec-cs-ritsumei-ac-jp.pickle'):
        os.remove(org_path + '/RAD/df_dict/falsification-cysec-cs-ritsumei-ac-jp.pickle')
    if os.path.exists(org_path + '/RAD/tag_data/falsification-cysec-cs-ritsumei-ac-jp.json'):
        os.remove(org_path + '/RAD/tag_data/falsification-cysec-cs-ritsumei-ac-jp.json')
    if os.path.exists(org_path + '/RAD/url_hash_json/falsification-cysec-cs-ritsumei-ac-jp.json'):
        os.remove(org_path + '/RAD/url_hash_json/falsification-cysec-cs-ritsumei-ac-jp.json')
    if os.path.exists(org_path + '/RAD/temp/progress_falsification-cysec-cs-ritsumei-ac-jp.pickle'):
        os.remove(org_path + '/RAD/temp/progress_falsification-cysec-cs-ritsumei-ac-jp.pickle')


# www.cysecからfalsification.cysecのデータを作成する
def copy_ROD_from_cysec(org_path):

    # 頻出単語、idf辞書はそのままコピー
    src_path = org_path + '/ROD/frequent_word_100/www-cysec-cs-ritsumei-ac-jp.json'
    if os.path.exists(src_path):
        shutil.copyfile(src_path, org_path + '/ROD/frequent_word_100/falsification-cysec-cs-ritsumei-ac-jp.json')

    src_path = org_path + '/ROD/idf_dict/www-cysec-cs-ritsumei-ac-jp.json'
    if os.path.exists(src_path):
        shutil.copyfile(src_path, org_path + '/ROD/idf_dict/falsification-cysec-cs-ritsumei-ac-jp.json')

    # tag_dataとurl_hash_jsonはkeyのURL部分を変更してコピー
    src_path = org_path + '/ROD/tag_data/www-cysec-cs-ritsumei-ac-jp.json'
    if os.path.exists(src_path):
        # readして書き換え
        with open(src_path, mode='r') as f:
            tag_data_dict = json.load(f)
        falsification_tag_dict = dict()
        for i, v in tag_data_dict.items():
            key = i.replace('www.cysec.cs.ritsumei.ac.jp', 'falsification.cysec.cs.ritsumei.ac.jp')
            falsification_tag_dict[key] = v
        # 保存
        with open(org_path + '/ROD/tag_data/falsification-cysec-cs-ritsumei-ac-jp.json', mode='w') as f:
            json.dump(falsification_tag_dict, f)

    src_path = org_path + '/ROD/url_hash_json/www-cysec-cs-ritsumei-ac-jp.json'
    if os.path.exists(src_path):
        # readして書き換え
        with open(src_path, mode='r') as f:
            url_hash_dict = json.load(f)
        falsification_hash_dict = dict()
        for i, v in url_hash_dict.items():
            key = i.replace('www.cysec.cs.ritsumei.ac.jp', 'falsification.cysec.cs.ritsumei.ac.jp')
            falsification_hash_dict[key] = v
        # 保存
        with open(org_path + '/ROD/url_hash_json/falsification-cysec-cs-ritsumei-ac-jp.json', mode='w') as f:
            json.dump(falsification_hash_dict, f)


if __name__ == '__main__':
    copy_ROD_from_cysec(org_path="/home/cysec/Desktop/crawler/organization/ritsumeikan")