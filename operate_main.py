from main import crawler_host
from tf_idf import make_idf_dict_frequent_word_dict, make_request_url_iframeSrc_link_host_set
from check_result.main_cr import del_and_make_achievement
# from SVC_screenshot import del_0size
from multiprocessing import Process, set_start_method, get_context
import os
import subprocess
import shutil
from falcification_dealing import del_falsification_RAD, copy_ROD_from_cysec
import sys
from datetime import datetime
from time import sleep


# 実行ディレクトリはcrawler_srcじゃないと、main_cr.pyのmake_achievement()のchdirでバグる?
# 例： python3 operate_main.py ritsumeikan


# 子プロセスを返す
def return_children(my_pid):
    try:
        children = subprocess.check_output(['ps', '--ppid', str(my_pid), '--no-heading', '-o', 'pid'])
    except subprocess.CalledProcessError:
        print('Non children')
        return list()
    else:
        print('me : ', my_pid)
        child_list = children.decode().replace(' ', '').split('\n')
        try:
            child_list.remove('')
        except ValueError:
            pass
        return child_list


# meより下の家族プロセスkillする
def kill_family():
    me = os.getpid()
    family = return_children(me)
    print(family)
    i = 0
    while True:
        pid_ = family[i]
        family.extend(return_children(pid_))
        print(family)
        i += 1
        if len(family) == i:
            break
    family.reverse()
    for kill_pid in family:
        os.system("kill -9 " + kill_pid)


# PPIDが1のphantomJSをkillする(クローラが動かしているphantomjsのppidは1以外なので、ppid=1のphantomjsはゾンビ的な)
def kill_phantomjs():
    os.system("pkill -KILL -P 1 -f 'phantomjs'")


def dealing_after_fact(org_arg):
    dir_name = org_arg['result_no']
    org_path = org_arg['org_path']

    # コピー先を削除
    shutil.rmtree(org_path + '/ROD/url_hash_json')
    shutil.rmtree(org_path + '/ROD/tag_data')

    # 偽サイトの情報を削除
    if org_path == '../organization/ritsumeikan':
        del_falsification_RAD(org_path=org_path)

    # 移動
    print('copy file to ROD from RAD : ', end='')
    shutil.copytree(org_path + '/RAD/df_dict', org_path + '/ROD/df_dicts/' +
                    str(len(os.listdir(org_path + '/ROD/df_dicts/')) + 1))
    shutil.move(org_path + '/RAD/url_hash_json', org_path + '/ROD/url_hash_json')
    shutil.move(org_path + '/RAD/tag_data', org_path + '/ROD/tag_data')
    shutil.move(org_path + '/RAD/url_db', org_path + '/ROD/url_db')
    """
    if os.path.exists('RAD/screenshots'):
        # スクショを撮っていたら、0サイズの画像を削除
        p = Process(target=del_0size.del_0size_and_rename, args=('RAD/screenshots',))
        p.start()
        p.join()
        if os.path.exists('ROD/screenshots'):
            shutil.rmtree('ROD/screenshots')
        shutil.move('RAD/screenshots', 'ROD/screenshots')
    print('done')
    """
    # tf_idf.pyの実行
    print('run function of tf_idf.py : ', end='')
    p = Process(target=make_idf_dict_frequent_word_dict, args=(org_path,))
    if org_path == '../organization/ritsumeikan':
        p2 = Process(target=make_request_url_iframeSrc_link_host_set, args=(org_path,))
        p2.start()
    else:
        p2 = None
    p.start()
    p.join()
    if p2 is not None:
        p2.join()
    print('done')

    # RADの削除
    print('delete RAD : ', end='')
    shutil.rmtree(org_path + '/RAD')
    print('done')

    # resultの移動
    print('move result to check_result : ', end='')
    path = org_path + '/result_history/' + dir_name
    shutil.move(src=org_path + '/result', dst=path)
    print('done')

    # main_cr.pyの実行
    del_and_make_achievement(path)

    # 偽サイトの情報をwww.cysec.cs.ritsumei.ac.jpからコピー
    if org_path == '../organization/ritsumeikan':
        copy_ROD_from_cysec(org_path=org_path)


def save_rod(org_arg):
    dir_name = org_arg['result_no']
    org_path = org_arg['org_path']

    if not os.path.exists(org_path + '/ROD_history'):
        os.mkdir(org_path + '/ROD_history')

    dst_dir = org_path + '/ROD_history/ROD_' + dir_name
    shutil.copytree(org_path + '/ROD', dst_dir)
    with open(dst_dir + '/read.txt', 'w') as f:
        f.writelines('This ROD directory is used by ' + dir_name + "'th crawling.")


def main(organization):
    # 以下のwhileループ内で
    # このファイル位置のパスを取ってきてchdirする
    # 実行ディレクトリはこのファイル位置じゃないとバグるかも(全て相対パスだから)
    now_dir = os.path.dirname(os.path.abspath(__file__))  # ファイル位置(check_resultディレクトリ)を絶対パスで取得
    os.chdir(now_dir)

    # 引数として与えられた組織名のディレクトリが存在するか
    org_path = '../organization/' + organization
    if not os.path.exists(org_path):
        print('You should check existing ' + organization + ' directory in ../organization/')
        return 0

    # 既に実行中ではないか
    if os.path.exists('../organization/' + organization + '/running.tmp'):
        print(organization + "'s site is crawled now.")
        return 0
    else:
        # 実行途中ではない場合、ファイルを作って実行中であることを示す
        f = open('../organization/' + organization + '/running.tmp', 'w', encoding='utf-8')
        start_time = datetime.now().strftime('%Y/%m/%d, %H:%M:%S')
        f.write(start_time)
        f.close()

    if not os.path.exists(org_path + '/result_history'):
        os.mkdir(org_path + '/result_history')
    dir_name = str(len(os.listdir(org_path + '/result_history')) + 1)

    org_arg = {'result_no': dir_name, 'org_path': org_path}

    while True:
        # クローラを実行
        print('--- ' + organization + ' : ' + org_arg['result_no'] + ' th crawling---')
        p = Process(target=crawler_host, args=(org_arg,))
        p.start()
        p.join()
        exitcode = p.exitcode
        if (exitcode == 255) or (exitcode < 0):  # エラー落ちの場合?
            print('operate_main ended by crawler error')
            break
        print('crawling has finished.')

        # 子プロセスが残る可能性がある?
        kill_family()
        kill_phantomjs()  # 特にPhantomJSは念入りに

        print('save used ROD before overwriting the ROD directory : ', end='')
        save_rod(org_arg)
        print('done')

        print('---dealing after fact---')
        dealing_after_fact(org_arg)

        print('--- ' + organization + ' : ' + org_arg['result_no'] + ' th crawling DONE ---')
        now = datetime.now()
        print(now)
        org_arg['result_no'] = str(int(org_arg['result_no']) + 1)
        print(organization + ' : ' + org_arg['result_no'] + ' th crawling will start at 20:00')

        # 実行ディレクトリ移動
        os.chdir(now_dir)
        break

    # 実行中であることを示すファイルを削除する
    if os.path.exists('../organization/' + organization + '/running.tmp'):
        os.remove('../organization/' + organization + '/running.tmp')


if __name__ == '__main__':
    # spawnで子プロセス生成
    set_start_method('spawn')

    args = sys.argv
    if len(args) != 2:
        print('need arg to choice organization.')

    main(organization=args[1])
