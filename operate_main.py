from main import crawler_host
from tf_idf import make_idf_dict_frequent_word_dict, make_request_url_iframeSrc_link_host_set
from check_result.main_cr import del_and_make_achievement
from SVC_screenshot import del_0size
from multiprocessing import Process
import os
import shutil


def get_user_input(queue):
    while True:
        end = input('enter "end" to end : ')
        if end == 'end':
            queue.put(True)
            break


def kill_process(queue, p):
    kill = queue.get(block=True)
    if kill is True:
        p.terminate()


def dealing_after_fact(dir_name):
    # コピー先を削除
    shutil.rmtree('ROD/url_hash_json')
    shutil.rmtree('ROD/tag_data')

    # 移動
    print('copy to ROD from RAD : ', end='')
    shutil.copy2('RAD/df_dict', 'ROD/df_dicts/' + str(len(os.listdir('ROD/df_dicts/')) + 1))
    shutil.move('RAD/url_hash_json', 'ROD/url_hash_json')
    shutil.move('RAD/tag_data', 'ROD/tag_data')
    if os.path.exists('RAD/screenshots'):
        # スクショを撮っていたら、0サイズの画像を削除
        p = Process(target=del_0size.del_0size_and_rename, args=('RAD/screenshots',))
        p.start()
        p.join()
        if os.path.exists('ROD/screenshots'):
            shutil.rmtree('ROD/screenshots')
        shutil.move('RAD/screenshots', 'ROD/screenshots')
    print('done')

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
    os.mkdir('ROD_history/' + dir_name)
    with open('ROD_history/' + dir_name + '/read.txt', 'w') as f:
        f.writelines('This ROD directory is used by ' + dir_name + ' crawling.')
    shutil.copytree('ROD/url_hash_json', 'ROD_history/' + dir_name + '/url_hash_json')
    shutil.copytree('ROD/tag_data', 'ROD_history/' + dir_name + '/tag_data')
    if os.path.exists('ROD/request_url'):
        shutil.copytree('ROD/request_url', 'ROD_history/' + dir_name + '/request_url')
    if os.path.exists('ROD/link_host'):
        shutil.copytree('ROD/link_host', 'ROD_history/' + dir_name + '/link_host')
    if os.path.exists('ROD/iframe_src'):
        shutil.copytree('ROD/iframe_src', 'ROD_history/' + dir_name + '/iframe_src')
    if os.path.exists('ROD/idf_dict'):
        shutil.copytree('ROD/idf_dict', 'ROD_history/' + dir_name + '/idf_dict')
    if os.path.exists('ROD/frequent_word_100'):
        shutil.copytree('ROD/frequent_word_100', 'ROD_history/' + dir_name + '/frequent_word_100')


def main():
    if not os.path.exists('check_result/result'):
        os.mkdir('check_result/result')
    dir_name = len(os.listdir('check_result/result')) + 1

    while True:
        print('---' + str(dir_name) + ' th crawling---')
        p = Process(target=crawler_host, args=(dir_name,))
        p.start()
        p.join()
        exitcode = p.exitcode
        if (exitcode == 255) or (exitcode < 0):  # エラー落ちの場合
            break
        print('crawling has finished.')

        print('save used ROD before overwriting the ROD directory : ', end='')
        save_rod(str(dir_name))
        print('done')

        print('---dealing after fact---')
        dealing_after_fact(str(dir_name))

        dir_name += 1


if __name__ == '__main__':
    main()
