import pandas as pd
import json


def get_words(path):
    with open(path, 'r') as f:
        word_list = json.load(f)
    return word_list


def main():
    path = '25/achievement/frequent_word_investigation.csv'
    row = list()

    with open(path) as f:
        f.readline()
        while True:
            line = f.readline()
            if line == '':
                break
            line = line[0:-1]
            row.append(line.split(','))
            if 'True' in line:
                print(line)
    word_list = get_words('../ROD/frequent_word_100/www-spc-ritsumei-ac-jp.json')
    return 0
    df = pd.DataFrame(row, columns=['URL', 'new', '10', '20', '30', '40', '50', 'error'])

    # URLに,が含まれているものがあるので調整する
    for key, value in df.iterrows():
        if value['error'] is not None:
            value['URL'] = value['URL'] + ',' + value['new']
            value['new'] = value['10']
            value['10'] = value['20']
            value['20'] = value['30']
            value['30'] = value['40']
            value['40'] = value['50']
            value['50'] = value['error']
    del df['error']

    # 各数字ごとの数をカウント
    dic = dict()
    for key, value in df.iterrows():
        for num in value.index:
            if num == 'URL' or num == 'new':
                continue
            if value[num] is None:
                continue
            if num in dic:
                if int(value[num]) in dic[num]:
                    dic[num][int(value[num])] += 1
                else:
                    dic[num][int(value[num])] = 1
            else:
                dic[num] = dict()
                dic[num][int(value[num])] = 1


    #
    for i, v in sorted(dic.items()):
        print(i, v)
        sort_key = sorted(v.items())

        df2 = pd.DataFrame([temp[1] for temp in sort_key], index=[temp[0] for temp in sort_key])
        df2.to_csv(str(i) + '_words.csv', header=None)


if __name__ == '__main__':
    main()
