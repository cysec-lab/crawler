import json
import os


def print_word_df(path):
    json_files = os.listdir(path)

    for json_file in json_files:
        with open(path + '/' + json_file, 'r') as f:
            df_dict = json.load(f)

        print('--- ' + json_file + ' ---')

        del_list = list()
        for word, df in df_dict.items():
            if len(word) == 1:
                if ('a' < word < 'z') or ('A' < word < 'Z'):
                    del_list.append(word)
                    print(word)
        for del_word in del_list:
            del df_dict[del_word]
        if 'http://' in df_dict:
            print('http://')
            del df_dict['http://']


def main():
    path = '../ROD/df_dicts/1'
    print_word_df(path)


if __name__ == '__main__':
    main()
