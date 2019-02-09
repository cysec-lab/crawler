# クローリング完了後、複数のresult_*に分かれて保存されているデータをまとめる

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
    file_dic = dict()

    os.chdir(dire)
    os.mkdir('achievement')
    lis = [result_dir for result_dir in os.listdir() if result_dir.startswith("result_")]  # result_*のディレクトリのリストを取得
    lis.sort()
    run_time = 0
    all_achievement = 0
    iframe_count = 0
    lock = True
    for result in lis:
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


# 各「result_*」ディレクトリの中の「server」の中のデータをサーバディレクトリごとにまとめる
def merge_server_dir(path):
    os.chdir(path)
    lis = [result_dir for result_dir in os.listdir() if result_dir.startswith("result_")]  # result_*のディレクトリのリストを取得
    lis.sort()

    # result_1のserverディレクトリをachievementにコピー
    shutil.copytree(path + "/" + lis[0] + "/server", path + "/achievement/server")

    for result_dir in lis[1:]:
        if not os.path.exists(path + "/" + result_dir + "/server"):
            continue
        servers = os.listdir(path + "/" + result_dir + "/server")
        achievement_servers = os.listdir(path + "/achievement/server")
        for server in servers:
            if not os.path.isdir(path + "/" + result_dir + "/server/" + server):
                continue
            if server in achievement_servers:
                files = os.listdir(path + "/" + result_dir + "/server/" + server)
                for file in files:
                    with open("{}/{}/server/{}/{}".format(path, result_dir, server, file), mode="r") as f:
                        content = f.read()
                    with open("{}/achievement/server/{}/{}".format(path, server, file), mode="a") as f:
                        f.write("\n" + content)
            else:
                shutil.copytree(path + "/" + result_dir + "/server/" + server, path + "/achievement/server/" + server)


def cal_num_of_achievement(path):
    os.chdir(path + "/achievement/server")
    lis = [server_dir for server_dir in os.listdir() if os.path.isdir(server_dir)]  # 各サーバディレクトリのリストを取得
    server_dic = dict()
    total_p = 0
    total_f = 0

    for server_dir in lis:
        with open(server_dir + "/achievement.txt", "r") as f:
            content = f.read()
        num = content.split("\n")[-1]
        page_num, file_num = num.split(",")
        num = int(page_num) + int(file_num)
        server_dic[server_dir] = ("{}(p: {}, f: {})".format(num, page_num, file_num), num)
        total_p += int(page_num)
        total_f += int(file_num)

    total = int(total_p) + int(total_f)
    server_dic["total"] = ("{}(p: {}, f: {})".format(total, total_p, total_f), total)
    content = ""
    for server, num in sorted(server_dic.items(), key=lambda x: x[1][1], reverse=True):
        content += "{}: {}\n".format(num[0], server)
    with open("num_of_achievement.txt", "w") as f:
        f.write(content)


# クローリング完了後、複数のresult/result_*に分かれて保存されているデータをまとめて、result/achievement/に保存する
# また、いらないtempファイルを削除する
def del_and_make_achievement(path):
    """
    :param path: org_path / result_history / *
    :return:
    """
    now_dir = os.path.dirname(os.path.abspath(__file__))  # ファイル位置を絶対パスで取得
    del_temp_file(path, 0, 0)
    del_dir(path, 0, 0)
    make_achievement(path)
    merge_server_dir(path)
    cal_num_of_achievement(path)

    os.chdir(now_dir)  # 実行ディレクトリに戻る


if __name__ == '__main__':
    cal_num_of_achievement(path="/home/cysec/Desktop/crawler/organization/ritsumeikan/result_history/1")
