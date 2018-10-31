from hashlib import sha256
import json
import os
from datetime import date
from copy import deepcopy
from shutil import copyfile


# url_dictの操作を行う。各Webサーバ毎に生成される。
# jsonで保存するため、set集合はlistにしている
class UrlDict:
    def __init__(self, host, org_path=""):
        self.host = host
        self.org_path = org_path
        self.url_dict = dict()      # url : そのURLの情報の辞書
        self.url_tags = dict()      # url : タグ順番保存

    def load_url_dict(self, path=None):
        copy_flag = ''
        rad_dir = self.org_path + '/RAD'
        rod_dir = self.org_path + '/ROD'
        # url_hashのロード
        if path is None:
            path = rad_dir + '/url_hash_json/' + self.host + '.json'
        else:
            path += self.host + '.json'    # test用
        if os.path.exists(path):
            if os.path.getsize(path) > 0:
                f = open(path, 'r')
                try:
                    self.url_dict = json.load(f)
                except json.decoder.JSONDecodeError:   # JSONデータが破損していた場合
                    f.close()
                    # RODから持ってくる
                    src = rod_dir + '/url_hash_json/' + self.host + '.json'
                    if os.path.exists(src):
                        copyfile(src, path)
                        f = open(path, 'r')
                        try:
                            self.url_dict = json.load(f)
                        except json.decoder.JSONDecodeError:   # RODも破損していた場合
                            f.close()
                            # 過去のRODから持ってくる
                            if os.path.exists(rod_dir + '_history'):
                                rod_lis = os.listdir(rod_dir + '_history')
                                latest_rods = sorted(rod_lis, reverse=True,
                                                     key=lambda dir_name: int(dir_name[dir_name.find('_') + 1:]))
                                for latest_rod in latest_rods:
                                    try:
                                        src = rod_dir + '_history/' + latest_rod + '/url_hash_json/' + self.host + '.json'
                                        if os.path.exists(src):
                                            copyfile(src, path)
                                            with open(path, 'r') as f:
                                                self.url_dict = json.load(f)
                                            copy_flag += ' url_hash from(' + latest_rod + ').'
                                    except json.decoder.JSONDecodeError:
                                        continue
                                    else:
                                        break
                                if not self.url_dict:
                                    copy_flag += ' url_hash has not loaded.'
                        else:
                            f.close()
                            copy_flag = ' url_hash from ROD.'
                else:
                    f.close()
        # tag_dataのロード
        path = rad_dir + '/tag_data/' + self.host + '.json'
        if os.path.exists(path):
            if os.path.getsize(path) > 0:
                f = open(path, 'r')
                try:
                    self.url_tags = json.load(f)
                except json.decoder.JSONDecodeError:   # JSONデータが破損していた場合
                    f.close()
                    # RODから持ってくる
                    src = rod_dir + '/tag_data/' + self.host + '.json'
                    if os.path.exists(src):
                        copyfile(src, path)
                        f = open(path, 'r')
                        try:
                            self.url_tags = json.load(f)
                        except json.decoder.JSONDecodeError:  # RODも破損していた場合
                            f.close()
                            # 過去のRODから持ってくる
                            if os.path.exists(rod_dir + '_history'):
                                rod_lis = os.listdir(rod_dir + '_history')
                                latest_rods = sorted(rod_lis, reverse=True,
                                                     key=lambda dir_name: int(dir_name[dir_name.find('_') + 1:]))
                                for latest_rod in latest_rods:
                                    try:
                                        src = rod_dir + '_history/' + latest_rod + '/tag_data/' + self.host + '.json'
                                        if os.path.exists(src):
                                            copyfile(src, path)
                                            with open(path, 'r') as f:
                                                self.url_tags = json.load(f)
                                            copy_flag += ' tag_data from(' + latest_rod + ').'
                                    except json.decoder.JSONDecodeError:
                                        continue
                                    else:
                                        break
                                if not self.url_tags:
                                    copy_flag += ' tag_data has not loaded.'
                        else:
                            f.close()
                            copy_flag += ' tag_data from ROD.'
                else:
                    f.close()
        return copy_flag

    def save_url_dict(self):
        data_dir = self.org_path + '/RAD'
        if len(self.url_dict) > 0:
            f = open(data_dir + '/url_hash_json/' + self.host + '.json', 'w')
            json.dump(self.url_dict, f)
            f.close()
        if len(self.url_tags) > 0:
            f = open(data_dir + '/tag_data/' + self.host + '.json', 'w')
            json.dump(self.url_tags, f)
            f.close()

    def add_tag_data(self, page, tags):
        if tags:
            if page.url in self.url_tags:
                if tags not in self.url_tags[page.url]:
                    if ('iframe' in tags) or ('invisible_iframe' in tags):
                        self.url_tags[page.url].append(tags)   # iframeタグは読み込まれたりされなかったりすることが多いため、iframeタグがある場合は全パターン保存
                    else:
                        self.url_tags[page.url][0] = tags    # iframeタグのないパターンは最新のものだけ保存
            else:
                if ('iframe' in tags) or ('invisible_iframe' in tags):
                    self.url_tags[page.url] = list([[], tags])    # tagリストのリスト(0番目はiframeタグのないものを入れる)
                else:
                    self.url_tags[page.url] = list([tags])    # tagリストのリスト

    def update_request_url_in_url_dict(self, page):
        if page.url in self.url_dict:
            # self.url_dict[page.url]['request_url_same_host'] = list(deepcopy(page.request_url_same_host))
            self.url_dict[page.url]["request_url"] = list(deepcopy(page.request_url))
        else:
            return False
        return True

    def compare_request_url(self, page):
        if page.url in self.url_dict:
            # if 'request_url_same_host' in self.url_dict[page.url]:
            #     diff = page.request_url_same_host.difference(set(self.url_dict[page.url]['request_url_same_host']))
            # else:
            #     diff = False
            diff = False
        else:
            diff = False
        return diff

    def add_top10_to_url_dict(self, url, top10):
        self.url_dict[url]['important_words'] = deepcopy(top10)

    def get_top10_from_url_dict(self, url):
        if url in self.url_dict:
            if 'important_words' in self.url_dict[url]:
                top10 = self.url_dict[url]['important_words']
                return top10
            else:
                return None
        else:
            return None

    # ハッシュ値を比較する。変わっていなければTrueを、変わっていると前回までの不変日数を返す。Falseは新規、Noneはエラー
    # 二つ目はファイルサイズが同じだったかどうか、全て読み込まれているかどうか分からないため(途中切断はなさそうなため不要?)
    def compere_hash(self, page):
        file_length = len(page.html)
        if file_length:
            if type(page.html) == str:
                try:
                    html_hash = page.html.encode('utf-8')
                except Exception:
                    return None, False
            else:
                html_hash = page.html
            try:
                sha = sha256(html_hash).hexdigest()
            except Exception:
                return None, False
        else:
            sha = None

        today = date.today()
        temp = str(today).split('-')
        y, m, d = temp
        today = [int(y), int(m), int(d)]
        if page.url in self.url_dict:
            pre_info = deepcopy(self.url_dict[page.url])
            self.url_dict[page.url]['hash'] = sha               # ハッシュ値
            self.url_dict[page.url]['file_length'] = file_length   # ファイルの長さを更新
            self.url_dict[page.url]['run_date'] = today            # 実行日を更新
            self.url_dict[page.url]['source'] = page.src           # URLのリンク元

            pre_sha = pre_info['hash']                             # 前回のハッシュ値
            pre_day = pre_info['run_date']                         # 前回のクローリング日
            pre_day = date(pre_day[0], pre_day[1], pre_day[2])     # dateクラス化
            date_difference = date.today() - pre_day               # 接続日と前回日との日にち差

            if pre_sha == sha:
                diff = pre_info['unchanged_num_of_days'] + date_difference.days
                self.url_dict[page.url]['unchanged_num_of_days'] = diff     # 不変日数を更新
                return True, 0
            else:
                self.url_dict[page.url]['unchanged_num_of_days'] = 0        # 不変日数を更新
                if pre_info['file_length']:
                    length_difference = file_length - pre_info['file_length']    # 今回と前回のファイルサイズ差
                else:
                    length_difference = None     # 前回のファイルサイズが0の場合
                return pre_info['unchanged_num_of_days'], length_difference
        else:
            self.url_dict[page.url] = dict()
            self.url_dict[page.url]['hash'] = sha
            self.url_dict[page.url]['file_length'] = file_length
            self.url_dict[page.url]['unchanged_num_of_days'] = 0
            self.url_dict[page.url]['run_date'] = today
            self.url_dict[page.url]['source'] = page.src
            return False, False
