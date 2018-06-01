import os
import json


def get_hash():
    os.chdir('../RAD/url_hash_json')
    host = os.listdir()
    for i in host:
        if not i == 'falsification-cysec-cs-ritsumei-ac-jp.json':
            continue
        with open(i, 'r') as f:
            url_dic = json.load(f)
    return url_dic


def tes():
    from mecab import get_tf_dict_by_mecab
    # このページの各単語のtf値を計算、df辞書を更新
    hack_level, word_tf_dict = get_tf_dict_by_mecab(soup)  # tf値の計算と"hacked by"検索
    if hack_level:  # hackの文字が入っていると0以外が返ってくる
        if hack_level == 1:
            update_write_file_dict('result', 'hack_word_Lv' + str(hack_level) + '.txt', content=page.url)
        else:
            data_temp = dict()
            data_temp['url'] = page.url
            data_temp['src'] = page.src
            data_temp['file_name'] = 'hack_word_Lv' + str(hack_level) + '.csv'
            data_temp['content'] = page.url + ',' + page.src
            data_temp['label'] = 'URL,SOURCE'
            with wfta_lock:
                write_file_to_alertdir.append(data_temp)
            # update_write_file_dict('alert', 'hack_word_Lv' + str(hack_level) + '.txt',
            #                        content=['URL,SOURCE', page.url + ',' + page.src])
    if word_tf_dict is not False:
        with word_df_lock:
            word_df_dict = add_word_dic(word_df_dict, word_tf_dict)  # サーバのidf計算のために単語と出現ページ数を更新
        if word_idf_dict:
            word_tfidf = make_tfidf_dict(idf_dict=word_idf_dict, tf_dict=word_tf_dict)  # tf-idf値を計算
            top10 = get_top10_tfidf(tfidf_dict=word_tfidf)  # top10を取得。ページ内に単語がなかった場合は空リストが返る
            # ハッシュ値が異なるため、重要単語を比較
            # if num_of_days is not True:
            if True:  # 実験のため毎回比較
                pre_top10 = urlDict.get_top10_from_url_dict(url=page.url)  # 前回のtop10を取得
                if pre_top10 is not None:
                    symmetric_difference = set(top10) ^ set(pre_top10)  # 排他的論理和
                    if len(symmetric_difference) > 16:
                        data_temp = dict()
                        data_temp['url'] = page.url
                        data_temp['src'] = page.src
                        data_temp['file_name'] = 'change_important_word.csv'
                        data_temp['content'] = page.url + ',' + str(top10) + ',' + str(pre_top10)
                        data_temp['label'] = 'URL,TOP10,PRE'
                        with wfta_lock:
                            write_file_to_alertdir.append(data_temp)
                        # update_write_file_dict('alert', 'change_important_word.csv',
                        #                        content=['URL,TOP10,PRE',
                        #                                 page.url + ',' + str(top10) + ',' + str(pre_top10)])
                    update_write_file_dict('result', 'symmetric_diff_of_word.csv',
                                           content=['URL,length,top10,pre top10', page.url + ',' +
                                                    str(len(symmetric_difference)) + ',' + str(top10) + ',' +
                                                    str(pre_top10) + ',' + str(num_of_days)])
            urlDict.add_top10_to_url_dict(url=page.url, top10=top10)  # top10を更新


if __name__ == '__main__':
    dic = get_hash()
    print(dic['http://falsification.cysec.cs.ritsumei.ac.jp/home/research'])
