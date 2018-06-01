import os
import shutil


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
