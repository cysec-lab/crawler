
import os
from file_rw import r_json, w_json, wa_file, r_file, w_file
import shutil
from check_result.normalize_dir import del_temp_file, del_pickle, del_dir


def print_url_tuple():
    data = r_json('URL_tuple')
    count = 0
    print('all = ' + str(len(data)))
    data_temp = data.copy()
    url_dict = {}
    for url in data:
        if 'http://www.ritsumei.ac.jp/acd/gr/gsshs/theme/pdf' in url[0]:
            count += 1
            data_temp.remove(url)
            print(url)
        if url[0].split('/')[2] in url_dict:
            url_dict[url[0].split('/')[2]][0] += 1
            url_dict[url[0].split('/')[2]][1] += url
        else:
            url_dict[url[0].split('/')[2]] = [1, url]

    print('the last len = ' + str(len(data)))
    print('remove = ' + str(count))
    for i, v in url_dict.items():
        print(i + '\t' + str(v[0]))
    #w_json('URL_tuple', data=data_temp)


def make_achievement(dire):
    now_dir = os.path.dirname(os.path.abspath(__file__))  # ファイル位置(check_resultディレクトリ)を絶対パスで取得

    file_dic = dict()
    os.chdir(dire)
    lis = os.listdir()
    lis.sort()
    os.mkdir('achievement')
    run_time = 0
    all_achievement = 0
    iframe_count = 0
    lock = True
    for result in lis:
        if not result.startswith('result_'):
            continue
        os.chdir(result)
        result_list = os.listdir()
        for j in range(len(result_list)):
            if result_list[j].endswith('.json'):
                continue
            elif result_list[j] == 'clamd_files':
                temp = os.listdir('clamd_files')
                if temp:
                    if not os.path.exists('../achievement/clamd_files'):
                        os.mkdir('../achievement/clamd_files')
                    for k in temp:
                        shutil.copyfile('clamd_files/' + k, '../achievement/clamd_files/' + str(len(os.listdir('../achievement/clamd_files/'))) + '.clamd')
                continue
            elif os.path.isdir(result_list[j]):
                continue
            else:
                try:
                    f = open(result_list[j], 'r', encoding='utf-8')
                    data = f.read()  # 改行文字は含まれる
                except UnicodeDecodeError:
                    try:
                        f = open(result_list[j], 'r', encoding='cp932')
                        data = f.read()  # 改行文字は含まれる
                    except UnicodeDecodeError:
                        data = ''
                finally:
                    f.close()
                    if result_list[j] in file_dic:
                        file_dic[result_list[j]] += data
                    else:
                        file_dic[result_list[j]] = data
                data = data.splitlines()
                if result_list[j] == 'result.txt':
                    for line in data:
                        if 'run time' in line:
                            run_time += int(line[11:])
                        if lock:
                            if 'all achievement' in line:
                                all_achievement = int(line[18:])
                            if 'remaining = 0' in line:
                                lock = False
                elif result_list[j] == 'num_of_checked_url_ByMachineLearning.txt':
                    for line in data:
                        if line.isdecimal():
                            iframe_count += int(line)
        os.chdir('..')

    data = '\n----------------------------------------------\nall achievement = ' + str(all_achievement) + '\nrun time = ' + str(run_time)
    file_dic['result.txt'] += data

    if 'num_of_checked_url_ByMachineLearning.txt' in file_dic:
        file_dic['num_of_checked_url_ByMachineLearning.txt'] += '\n' + str(iframe_count) + ' pages including iframe.'

    for key, value in file_dic.items():
        wa_file('achievement/' + key, value)

    os.chdir(now_dir)  # check_resultにとぶ
    os.chdir('..')     # 実行ディレクトリにとぶ


def print_assignment():
    data = r_json('assignment')
    assignment = set(data)
    count = 0
    ritsu = list()
    print(len(assignment))
    for i in list(assignment):
        if 'http://www.ritsumei.ac.jp/acd/gr/gsshs//theme/pdf' in i:
            count += 1
            ritsu.append(i)
            #print(i)
    print(count)
    """
    diff = assignment.difference(assignment2)
    lis = list(diff)
    lis_sorted = sorted(lis)
    dic = {}
    for url in lis_sorted:
        o = urlparse(url)
        hostName = o.netloc
        if hostName in dic:
            dic[hostName].append(url)
        else:
            dic[hostName] = [url]
    for i in dic['www.ritsumei.ac.jp']:
        print(i)
    """


def print_sym_word():
    data = r_file('achievement/symmetric_diff_of_word.csv', mode='rb')
    data = data.decode('utf-8')
    lis = data.split('\r\n')

    num_dict = {}
    num_of_no_chage_hash = {}
    for line in lis:
        if line and line != 'URL,length,top10,pre top10':
            b = line.split(",[")
            num = b[0].split(',')[-1]
            try:
                num = int(num)
            except:
                continue
            if num in num_dict:
                num_dict[num].append(line)
                if line[line.rfind(',')+1:] == 'True':
                    if num in num_of_no_chage_hash:
                        num_of_no_chage_hash[num] += 1
                    else:
                        num_of_no_chage_hash[num] = 1
            else:
                num_dict[num] = [line]
                if line[line.rfind(',')+1:] == 'True':
                    num_of_no_chage_hash[num] = 1
    count = 0
    for i in sorted(num_dict.keys()):
        print(str(i) + ' : ' + str(len(num_dict[i])), end='')
        if i in num_of_no_chage_hash:
            print('\t : same hash pages = ' + str(num_of_no_chage_hash[i]))
        else:
            print('')
        count += len(num_dict[i])
    print('sum = ' + str(count))
    #for i in num_dict[20]:
        #print(i)


def print_changed_important_word():
    data = r_file('alert/change_important_word.csv', mode='rb')
    data = data.decode('utf-8')
    lis = data.split('\r\n')
    for i in lis:
        print(i)
    print(len(lis))


def del_and_make_achievement(path):
    del_temp_file(path, 0, 0)
    del_dir(path, 0, 0)
    make_achievement(path)


if __name__ == '__main__':
    s = os.path.dirname(os.path.abspath(__file__))
    print(s)
    """
    del_and_make_achievement(path='result/1')
    
    #os.chdir('../result/result_4')
    #print_url_tuple()
    #print_assignment()
    #get_result()
    #get_hash()

    os.chdir(dire)
    #print_sym_word()
    print_changed_important_word()
    """


def type_count(x):
    os.chdir(str(x) + '/result_1/server')
    listdir = os.listdir()
    for i in listdir:
        contntType_count = dict()
        data = r_file(i + '/content-type.txt')
        lis = data.split('\n')
        for j in lis:
            if j == '':
                continue
            if j[0:j.find(',')] in contntType_count:
                contntType_count[j[0:j.find(',')]] += 1
            else:
                contntType_count[j[0:j.find(',')]] = 1
        for key in contntType_count.keys():
            wa_file(i + '/content-type_count.csv', key + ',' + str(contntType_count[key]) + '\n')


def combine_num(x, y):
    server_achievement = dict()
    for i in range(x, y+1):
        try:
            data = r_file(str(i) + '/result_1/num.csv')
            print(data)
        except:
            continue
        lis = data.split('\n')
        for v in lis:
            if v[0:v.find(',')] in server_achievement:
                server_achievement[v[0:v.find(',')]].append(v[v.find(',')+1:])
            else:
                server_achievement[v[0:v.find(',')]] = [v[v.find(',') + 1:]]

    for key, value in server_achievement.items():
        if key != '':
            wa_file('result.csv', key)
            for j in value:
                wa_file('result.csv', ',' + str(j))
            wa_file('result.csv', '\n')

    for i in server_achievement['']:
        wa_file('result.csv', '総URL数,' + str(i))


def make_num(x):
    os.chdir(str(x) + '/result_1/server')
    count = 0
    listdir = os.listdir()
    for i in listdir:
        data = r_file(i + '/achievement.txt')
        count += int(data)
        wa_file('../num.csv', i + ',' + data + '\n')
    wa_file('../num.csv', ',' + str(count))
