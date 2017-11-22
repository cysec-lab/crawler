from main import crawler_host
from tf_idf import make_idf_dict_frequent_word_dict, make_request_url_iframeSrc_link_host_set
from check_result.main_cr import del_and_make_achievement
# from SVC_screenshot import del_0size
from multiprocessing import Process, set_start_method, get_context
import os
import subprocess
import shutil


def get_user_input(queue):
    while True:
        end = input('enter "end" to end : ')
        if end == 'end':
            queue.put(True)
            break


# 自分以外のpythonプロセスをkillする
def kill_python():
    re = subprocess.check_output(['pgrep', 'python'])
    me = os.getpid()
    re = re.decode().split('\n')
    re.remove(str(me))
    for py3 in re:
        os.system("kill " + py3)


def kill_phantomjs():
    os.system("pkill -f 'phantomjs'")


def dealing_after_fact(dir_name):
    # コピー先を削除
    shutil.rmtree('ROD/url_hash_json')
    shutil.rmtree('ROD/tag_data')

    # 移動
    print('copy to ROD from RAD : ', end='')
    shutil.copytree('RAD/df_dict', 'ROD/df_dicts/' + str(len(os.listdir('ROD/df_dicts/')) + 1))
    shutil.move('RAD/url_hash_json', 'ROD/url_hash_json')
    shutil.move('RAD/tag_data', 'ROD/tag_data')
    shutil.move('RAD/url_db', 'ROD/url_db')
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
    p = Process(target=make_idf_dict_frequent_word_dict)
    p2 = Process(target=make_request_url_iframeSrc_link_host_set)
    p.start()
    p2.start()
    p.join()
    p2.join()
    print('done')

    # RADの削除
    print('delete RAD : ', end='')
    shutil.rmtree('RAD')
    print('done')

    # resultの移動
    print('move result to check_result : ', end='')
    path = 'check_result/result/' + dir_name
    shutil.move(src='result', dst=path)
    print('done')

    # main_cr.pyの実行
    del_and_make_achievement(path)


def save_rod(dir_name):
    if not os.path.exists('ROD_history'):
        os.mkdir('ROD_history')

    dst_dir = 'ROD_history/' + dir_name
    os.mkdir(dst_dir)
    with open(dst_dir + '/read.txt', 'w') as f:
        f.writelines('This ROD directory is used by ' + dir_name + ' crawling.')
    shutil.copytree('ROD/url_hash_json', dst_dir + '/url_hash_json')
    shutil.copyfile('ROD/url_db', dst_dir + '/url_db')
    if os.path.exists('ROD/tag_data'):
        shutil.copytree('ROD/tag_data', dst_dir + '/tag_data')
    if os.path.exists('ROD/request_url'):
        shutil.copytree('ROD/request_url', dst_dir + '/request_url')
    if os.path.exists('ROD/link_host'):
        shutil.copytree('ROD/link_host', dst_dir + '/link_host')
    if os.path.exists('ROD/iframe_src'):
        shutil.copytree('ROD/iframe_src', dst_dir + '/iframe_src')
    if os.path.exists('ROD/idf_dict'):
        shutil.copytree('ROD/idf_dict', dst_dir + '/idf_dict')
    if os.path.exists('ROD/frequent_word_100'):
        shutil.copytree('ROD/frequent_word_100', dst_dir + '/frequent_word_100')


def main():
    print(get_context())

    if not os.path.exists('check_result/result'):
        os.mkdir('check_result/result')
    dir_name = len(os.listdir('check_result/result')) + 1

    while True:
        print('---' + str(dir_name) + ' th crawling---')
        p = Process(target=crawler_host, args=(dir_name,))
        p.start()
        p.join()
        exitcode = p.exitcode
        if (exitcode == 255) or (exitcode < 0):  # エラー落ちの場合?
            print('operate_main end with crawler error')
            break
        print('crawling has finished.')

        print('kill PhantomJS')
        kill_phantomjs()

        print('kill other python')
        kill_python()

        print('save used ROD before overwriting the ROD directory : ', end='')
        save_rod(str(dir_name))
        print('done')

        print('---dealing after fact---')
        dealing_after_fact(str(dir_name))

        dir_name += 1


if __name__ == '__main__':
    # spawnで子プロセス生成
    set_start_method('spawn')

    main()
