import os
import shutil

from utils.file_rw import r_file, w_file

# クローリング完了後、複数のresult_*に分かれて保存されているデータをまとめる

def del_temp_file(path: str, j: int, k: int):
    """
    result/result_*の中の途中保存ファイルを削除
    - jsonファイル
    - pickleファイル(waitingリストなど)

    args:
        path: org_path / result_history / *
        j: 消しはじめのresult_*番号
        k: result_* の数(0 = 不明)
    """
    if j == 0 and k == 0:
        # result_* の数を数える
        lis = os.listdir(path)
        for i in lis:
            if i.startswith('result_'):
                k += 1

        # 最後は消したくない可能性
        k -= 1
        j = 1
    # 削除していく
    for i in range(j, k + 1):
        temp_lis = os.listdir(path + '/result_' + str(i))
        for tempppp in temp_lis:
            # Jsonファイルを処理する
            if tempppp.endswith('.json'):
                try:
                    os.remove(path + '/result_' + str(i) + '/' + tempppp)
                except:
                    pass
            # .pickleファイル
            elif tempppp.endswith('.pickle'):
                try:
                    os.remove(path + '/result_' + str(i) + '/' + tempppp)
                except:
                    pass


def del_pickle(path: str):
    """
    未使用
    """
    num = os.listdir(path)
    for i in num:
        if i.startswith('result_'):
            server_list = os.listdir(path + '/' + i + '/server')
            for dirc in server_list:
                try:
                    os.remove(path + '/' + i + '/server' + dirc + '/temp_achievement.pickle')
                except:
                    pass


def del_dir(path: str, j: int, k: int):
    """
    path内のresult_*ディレクトリ下のディレクトリを削除
    例外: clamd, serverディレクトリ

    args:
        path: org_path/result_history/*/
        j: 消しはじめのresult_*番号
        k: result_* の数(0 = 不明)
    """
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


def make_achievement(dire: str):
    """
    result_history/*/下にachieventディレクトリを作る
    result直下のファイルから読み出したデータをachievementにまとめる

    args:
        dire: organization/result_history/*/ へのパス
    """
    file_dic: dict[str, str] = dict()

    os.chdir(dire)
    os.mkdir('achievement')
    # lisにresult/result_*のディレクトリのリストを格納
    lis = [result_dir for result_dir in os.listdir() if result_dir.startswith("result_")]
    lis.sort()
    run_time = 0
    all_achievement = 0
    lock = True
    for result in lis:
        os.chdir(result)
        result_list = os.listdir()
        for j in range(len(result_list)):
            # if result_list[j].endswith('.json'):
            #     continue
            if os.path.isdir(result_list[j]):
                continue
            else:
                data = r_file(result_list[j], mode="r")
                if data is None:
                    data = ""
                # result直下にあるファイルから読み出したデータをfile_dict[ファイル名]に追加する
                if result_list[j] in file_dic:
                    file_dic[result_list[j]] += data
                else:
                    file_dic[result_list[j]] = data
                data = data.splitlines()

                # 各回の詳細データが保存されている result.txt ファイルは中身を計算して修正する
                if result_list[j] == 'result.txt':
                    file_dic['result.txt'] += '\n'
                    for line in data:
                        if 'run time' in line:
                            run_time += int(line[11:])
                        if lock:
                            if 'all achievement' in line:
                                all_achievement = int(line[18:])
                            if 'remaining = 0' in line:
                                lock = False
                # elif result_list[j] == 'num_of_checked_url_ByMachineLearning.txt':
                #     for line in data:
                #         if line.isdecimal():
                #             iframe_count += int(line)
        # result_history/*/ に戻る
        os.chdir('..')

    # result_history/*/achevemnt/result.txt に書き込む辞書に合計探索数と時間を追記
    data = '\n----------------------------------------------\nall achievement = ' + str(all_achievement) + '\nrun time = ' + str(run_time)
    if 'result.txt' in file_dic:
        file_dic['result.txt'] += data
    else:
        file_dic['result.txt'] = data

    # if 'num_of_checked_url_ByMachineLearning.txt' in file_dic:
    #     file_dic['num_of_checked_url_ByMachineLearning.txt'] += '\n' + str(iframe_count) + ' pages including iframe.'

    # 実際のファイルと中身を作成する
    for key, value in file_dic.items():
        w_file('achievement/' + key, value, mode="a")


def merge_server_dir(path: str):
    """
    各「result_*」ディレクトリの中の「server」の中のデータをサーバディレクトリごとにまとめる

    args:
        path: organization/result_history/*/ のパス
    """
    os.chdir(path)
    # result_*のディレクトリのリストを取得
    lis = [result_dir for result_dir in os.listdir() if result_dir.startswith("result_")]
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
                # ディレクトリ以外(after_redirect.csv等)なら処理しない
                continue
            if server in achievement_servers:
                # すでに追加しようとしているサーバがachievementに存在するなら
                files = os.listdir(path + "/" + result_dir + "/server/" + server)
                for file in files:
                    # ファイルの中身を追記
                    with open("{}/{}/server/{}/{}".format(path, result_dir, server, file), mode="r") as f:
                        content = f.read()
                        if file.endswith('.csv'):
                            # CSVファイルの時はヘッダを取り除く
                            content = content[content.find('\n'):]
                    with open("{}/achievement/server/{}/{}".format(path, server, file), mode="a") as f:
                        f.write("\n" + content)
            else:
                # まだachievement内に存在しないサーバならそのままコピー
                shutil.copytree(path + "/" + result_dir + "/server/" + server, path + "/achievement/server/" + server)


def cal_num_of_achievement(path: str):
    """
    各サーバのページ到達数とファイル到達数, 合計数を数える
    /result_history/*/achievement/server/num_of_achievement.txtに記録

    args:
        path: organization/<>/result_history/ へのパス
    """
    os.chdir(path + "/achievement/server")
    # 各サーバディレクトリのリストを取得
    lis = [server_dir for server_dir in os.listdir() if os.path.isdir(server_dir)]
    server_dic: dict[str, tuple[str, int]] = dict()
    total_page = 0
    total_file = 0

    for server_dir in lis:
        # 各サーバのachievement.txtを開く
        try:
            with open(server_dir + "/achievement.txt", "r") as f:
                content = f.read()
            num = content.split("\n")[-1]
            page_num, file_num = num.split(",")
            num = int(page_num) + int(file_num)
            server_dic[server_dir] = ("{}(p: {}, f: {})".format(num, page_num, file_num), num)
            total_page += int(page_num)
            total_file += int(file_num)
        except FileNotFoundError:
            # 子プロセスが検査を終了する前に結果まとめ処理が始まってしまうのでえらる
            # そのうち子プロセス側から検査したURLを消すように変更する
            with open(path + "errors.txt", "a") as f:
                f.write("Error : cal_num_of_achievement failed to open " + server_dir + "achievement.txt / FileNotFoundError")

    total = int(total_page) + int(total_file)
    server_dic["total"] = ("{}(p: {}, f: {})".format(total, total_page, total_file), total)
    content = ""
    for server, num in sorted(server_dic.items(), key=lambda x: x[1][1], reverse=True):
        content += "{}: {}\n".format(num[0], server)
    with open("num_of_achievement.txt", "w") as f:
        f.write(content)


def del_and_make_achievement(path: str):
    """
    クローリング完了後に実行
    result/result_*に分けて保存されているデータをまとめて、result/achievement/に保存
    不要なtempファイルを削除する

    args:
        path: org_path /result_history/*/
    """

    # ファイル位置を絶対パスで取得
    now_dir = os.path.dirname(os.path.abspath(__file__))
    del_temp_file(path, 0, 0)
    del_dir(path, 0, 0)
    make_achievement(path)
    merge_server_dir(path)
    cal_num_of_achievement(path)

    # 実行ディレクトリに戻る
    os.chdir(now_dir)

if __name__ == '__main__':
    cal_num_of_achievement(path="/home/cysec/Desktop/crawler/organization/ritsumeikan/result_history/1")
