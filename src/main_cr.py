import os
import shutil
from file_rw import r_file, w_file

# result/result_*の中の途中保存jsonファイルとpickleファイルを削除する(waitingリストなど)
def del_temp_file(path, j, k):
    if j == 0 and k == 0:
        lis = os.listdir(path)
        for i in lis:
            if i.startswith('result_'):
                k += 1
        k -= 1   # 最後は消したくない可能性
        j = 1
    for i in range(j, k+1):
        temp_lis = os.listdir(path + '/result_' + str(i))
        for tempppp in temp_lis:
            if tempppp.endswith('.json'):
                try:
                    os.remove(path + '/result_' + str(i) + '/' + tempppp)
                except:
                    pass
            elif tempppp.endswith('.pickle'):
                try:
                    os.remove(path + '/result_' + str(i) + '/' + tempppp)
                except:
                    pass


def del_pickle(path):
    num = os.listdir(path)
    for i in num:
        if i.startswith('result_'):
            server_list = os.listdir(path + '/' + i + '/server')
            for dirc in server_list:
                try:
                    os.remove(path + '/' + i + '/server' + dirc + '/temp_achievement.pickle')
                except:
                    pass


# path内のresult_*ディレクトリ内のclamdとserver以外のディレクトリを削除する
# TEMPディレクトリだけ削除？
def del_dir(path, j, k):
    if j == 0 and k == 0:
        lis = os.listdir(path)
        for i in lis:
            if i.startswith('result_'):
                k += 1
        k -= 1   # 最後は消したくない可能性
        j = 1
    for i in range(j, k+1):
        lis = os.listdir(path + '/result_' + str(i))
        for d in lis:
            if os.path.isdir(path + '/result_' + str(i) + '/' + d):
                if d.startswith('clamd') or d.startswith('server'):
                    continue
                else:
                    try:
                        shutil.rmtree(path + '/result_' + str(i) + '/' + d)
                    except:
                        pass


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
            elif os.path.isdir(result_list[j]):
                continue
            else:
                data = r_file(result_list[j], mode="r")
                if data is None:
                    data = ""
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
        w_file('achievement/' + key, value, mode="a")

    os.chdir(now_dir)  # check_resultにとぶ
    os.chdir('..')     # 実行ディレクトリにとぶ


def del_and_make_achievement(path):
    del_temp_file(path, 0, 0)
    del_dir(path, 0, 0)
    make_achievement(path)
