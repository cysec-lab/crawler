import json
from random import randint


def get_tags(path):
    tags_list = list()
    url_list = list()
    # ファイルオープン
    with open(path, 'r') as f:
        url_dict = json.load(f)

    for key, value in url_dict.items():
        for v in value:   # valueは今までのtagリストのリストになってる
            if v:         # tagリストが空じゃなければ
                tags_list.append(v)
                url_list.append(key)
    return tags_list, url_list


# ひとつのURLから複数のベクトルを作成
def make_data(tags, tag_label, url, sample, sample2, crawling=False):
    vec_list = list()
    label_list = list()
    # タグリストをラベルリストに
    tag_label_list = list()
    for tag in tags:
        if tag in tag_label:
            ind = tag_label[tag]
        else:
            ind = tag_label['NewTag']
        tag_label_list.append(ind)

    # タグの前後sample個をベクトルにする
    length = len(tag_label_list)
    for i in range(0, length):
        if i <= sample:  # 最初のsample個
            continue
            vec = tag_label_list[0:sample+sample+1]
            vec.pop(i)
        elif (sample < i) and (i < length - sample):
            vec = tag_label_list[i-sample:i] + tag_label_list[i+1:i+sample+1]
            if sample2:
                vec.extend(tag_label_list[i-sample2:i] + tag_label_list[i+1:i+sample2+1])
        else:  # 最後のsample個
            vec = tag_label_list[-sample - sample - 1:]
            ind = length - i
            vec.pop(sample + sample - ind + 1)
            if sample2:
                if i + sample2 + 1 > length:
                    vec.extend(tag_label_list[-sample2 - sample2 - 1:])
                    vec.pop(sample + sample + sample2 + 1)
                else:
                    vec.extend(tag_label_list[i - sample2:i] + tag_label_list[i + 1:i + sample2 + 1])

        if '!kaizan!' in url:
            # !kaizan!urlはベクトルの中にiframeが入っているか、iframeのベクトルだけを保存
            if (-1 in vec) or (-2 in vec) or (tag_label_list[i] < 0):  # iframeのタグは負数が割り当てられている
                vec_list.append(vec)
                if tag_label_list[i] == -1:      # iframe
                    label_list.append([1, url])
                elif tag_label_list[i] == -2:    # invisible_iframe
                    label_list.append([2, url])
                else:
                    label_list.append([0, url])
        elif crawling:
            # クローリング中のurlはベクトルの中にiframe周辺のベクトルだけを保存
            if (-1 in vec) or (-2 in vec) or (tag_label_list[i] < 0):  # iframeのタグは負数が割り当てられている
                vec_list.append(vec)
                if tag_label_list[i] == -1:      # iframe
                    label_list.append([1, url])
                elif tag_label_list[i] == -2:    # invisible_iframe
                    label_list.append([2, url])
                else:
                    label_list.append([0, url])
        elif 'www.ritsumei.ac.jp' in url:  # このサーバは量が多すぎるので削る
            if (-1 in vec) or (-2 in vec) or (tag_label_list[i] < 0):  # iframeのタグは負数が割り当てられている
                vec_list.append(vec)
                if tag_label_list[i] == iframe:
                    label_list.append([1, url])
                else:
                    label_list.append([0, url])
            else:
                rand = randint(0, 2)
                if rand == 1:
                    vec_list.append(vec)
                    if tag_label_list[i] == iframe:
                        label_list.append([1, url])
                    else:
                        label_list.append([0, url])
        else:
            vec_list.append(vec)
            if tag_label_list[i] == -1:     # iframe
                label_list.append([1, url])
            elif tag_label_list[i] == -2:   # invisible_iframe
                label_list.append([2, url])
            else:
                label_list.append([0, url])
        """
        """
    return vec_list, label_list


def make_training_data(target_server, path, tag_label, sample, sample2):
    training_data = list()
    label_identifier = list()
    tags_list, url_list = get_tags(path + '/' + target_server)

    kaizan_data = list()
    kaizan_identifier = list()

    for i in range(len(tags_list)):
        if len(tags_list[i]) > sample*2:
            vec, label = make_data(tags_list[i], tag_label, url_list[i], sample=sample, sample2=sample2)
            if '!kaizan!' in url_list[i]:
                kaizan_data.extend(vec)
                kaizan_identifier.extend(label)
            else:
                training_data.extend(vec)
                label_identifier.extend(label)
    # ベクトルを作れるタグがひとつもなかった場合、iframeが含まれていたらNone、含まれていなければFalse
    if len(training_data) == 0:
        for tags in tags_list:
            if (-1 in tags) or (-2 in tags):
                return None, None, None
        return False, False, False

    # !kaizan!データ以外のiframeタグのデータをテストデータにするためにもう一度追加
    flag = True
    for i in range(len(label_identifier)):
        if label_identifier[i][0]:
            kaizan_data.append(training_data[i])
            kaizan_identifier.append(label_identifier[i])
            flag = False
    if flag:   # !kaizan!以外にiframeタグが見つからなかった場合
        return False, False, False
    else:
        training_data.extend(kaizan_data)
        label_identifier.extend(kaizan_identifier)

    return training_data, label_identifier, len(kaizan_data)


def preparation_main(target_server, path, tag_label, sample, sample2):
    training_data, label_identifier, kaizan_length = make_training_data(target_server=target_server, path=path,
                                                                        tag_label=tag_label, sample=sample,
                                                                        sample2=sample2)

    return training_data, label_identifier, kaizan_length
