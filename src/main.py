from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime
from logging import getLogger
from multiprocessing import Process, Queue, set_start_method
from typing import Any, Dict, Optional

from crawler_deinit import del_and_make_achievement
from crawler_init import crawler_host
from falcification_dealing import copy_ROD_from_cysec, del_falsification_RAD
from logger import (log_listener_configure, log_listener_process,
                    worker_configurer)
from make_filter_from_past_data import (
    make_filter, make_idf_dict_frequent_word_dict,
    make_request_url_iframeSrc_link_host_set, merge_filter)
from sys_command import kill_chrome

queue_log: Queue[Any] = Queue(-1)
logger = getLogger(__name__)

def dealing_after_fact(org_arg: Dict[str,str]):
    dir_name = org_arg['result_no']
    org_path = org_arg['org_path']

    # 偽サイトの情報を削除
    if '/organization/ritsumeikan' in org_path:
        del_falsification_RAD(org_path=org_path)

    # コピー先を削除
    shutil.rmtree(org_path + '/ROD/url_hash_json')
    shutil.rmtree(org_path + '/ROD/tag_data')

    # 移動
    logger.info('copy file to ROD from RAD : START')
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
    """
    logger.info('copy file to ROD from RAD : DONE')

    # make_filter_from_past_data.pyの実行 (tfidfの計算には少し時間(1分くらい)がかかるのでプロセスを分けて
    logger.info('Run function of tf_idf.py : START')
    p = Process(target=make_idf_dict_frequent_word_dict, args=(queue_log, org_path,)) # type: ignore
    p.start()

    # 立命館サイトは make_host_set()を自動で実行。
    # 今回の収集データと過去のデータをマージする作業なので、自動実行すると、今回検出された外部URLが安全なURLとして登録されてしまうため
    # ちゃんと人が判断してから追加したほうがいい。立命館サイトは面倒なので自動でやっちゃう。
    if '/organization/ritsumeikan' in org_path:
        p2 = Process(target=make_request_url_iframeSrc_link_host_set, args=(queue_log, org_path,)) # type: ignore
        p2.start()
    else:
        p2 = None

    p.join()
    if p2 is not None:
        p2.join()
    logger.info('Run function of tf_idf.py : DONE')

    # alertされたデータから新しいフィルタを作る (linkとrequest URL用
    logger.info('Making Filter             : START')
    make_filter(org_path=org_path)
    if '/organization/ritsumeikan' in org_path:  # 立命館サイトは merge_filter()を自動で実行。
        merge_filter(org_path=org_path)
    logger.info('Making Filter             : DONE')

    # RADの削除
    logger.info('delete RAD                : START')
    shutil.rmtree(org_path + '/RAD')
    logger.info('delete RAD                : DONE')

    # resultの移動
    logger.info('mv result to check_result : START')
    result_history_path = org_path + '/result_history/' + dir_name
    shutil.move(src=org_path + '/result', dst=result_history_path)
    logger.info('mv result to check_result : DONE')

    # crawler_deinit.pyの実行
    del_and_make_achievement(result_history_path)

    # 偽サイトの情報をwww.cysec.cs.ritsumei.ac.jpからコピー
    if '/organization/ritsumeikan' in org_path:
        copy_ROD_from_cysec(org_path=org_path)


def save_rod(org_arg: Dict[str, str]):
    dir_name = org_arg['result_no']
    org_path = org_arg['org_path']

    if not os.path.exists(org_path + '/ROD_history'):
        os.mkdir(org_path + '/ROD_history')

    dst_dir = org_path + '/ROD_history/ROD_' + dir_name
    shutil.copytree(org_path + '/ROD', dst_dir)
    with open(dst_dir + '/read.txt', 'w') as f:
        f.writelines(['This ROD directory is used by ' + dir_name + "'th crawling."])


def main(organization: str):
    # 以下のwhileループ内で
    # このファイル位置のパスを取ってきてchdirする
    # 実行ディレクトリはこのファイル位置じゃないとバグるかも(ほぼ全て相対パスだから)
    now_dir = os.path.dirname(os.path.abspath(__file__))  # ファイル位置(src)を絶対パスで取得
    os.chdir(now_dir)

    # Logger の作成
    log_listener = Process(target=log_listener_process,
                    args=(now_dir, queue_log, log_listener_configure))
    log_listener.start()
    worker_configurer(queue_log, logger)

    # 引数として与えられた組織名のディレクトリが存在するか
    organization_path = now_dir[0:now_dir.rfind('/')] + '/organization/' + organization
    if not os.path.exists(organization_path):
        logger.warning('You should check existing %s directory in ../organization/', organization)
        queue_log.put_nowait(None)
        log_listener.join()
        return 0

    # 既に実行中ではないか
    if os.path.exists(organization_path + '/running.tmp'):
        logger.warning("%s's site is crawled now.", organization)
        queue_log.put_nowait(None)
        log_listener.join()
        return 0
    else:
        # 実行途中ではない場合、ファイルを作って実行中であることを示す
        f = open(organization_path + '/running.tmp', 'w', encoding='utf-8')
        start_time = datetime.now().strftime('%Y/%m/%d, %H:%M:%S')
        f.write(start_time)
        f.close()

    # result_historyディレクトリがなければ作成
    if not os.path.exists(organization_path + '/result_history'):
        os.mkdir(organization_path + '/result_history')
    dir_name = str(len(os.listdir(organization_path + '/result_history')) + 1)

    org_arg = {'result_no': dir_name, 'org_path': organization_path}

    while True:
        # クローラを実行
        logger.info("""
    --- %s : %s th crawling---""", organization, org_arg['result_no'])
        p = Process(target=crawler_host, args=(queue_log, org_arg))
        p.start()
        p.join()
        exitcode: Optional[int] = p.exitcode
        if (exitcode == 255) or (exitcode < 0):
            # エラー落ちの場合?
            logger.error('operate_main ended by crawler error')
            break
        logger.info('crawling has finished.')

        # 孤児のchrome じゃなくてfirefoxをkill
        kill_chrome(queue_log, process='geckodriver')
        kill_chrome(queue_log, process='firefox')

        logger.info('save used ROD before overwriting the ROD directory : START')
        save_rod(org_arg)
        logger.info('save used ROD before overwriting the ROD directory : DONE')

        logger.info('---dealing after fact---')
        dealing_after_fact(org_arg)

        now = datetime.now()
        logger.info(f"""
    --- {organization} : {org_arg['result_no']} th crawling DONE ---
    {now}""")
        org_arg['result_no'] = str(int(org_arg['result_no']) + 1)
        logger.info(f"{organization} : {org_arg['result_no']} th crawling will start at 20:00")

        # 実行ディレクトリ移動
        os.chdir(now_dir)
        break

    # 実行中であることを示すファイルを削除する
    if os.path.exists(organization_path + '/running.tmp'):
        os.remove(organization_path + '/running.tmp')

    # Logを集めるリスナーを終了させる
    queue_log.put_nowait(None)
    log_listener.join()


if __name__ == '__main__':
    args = sys.argv
    if len(args) != 2:
        print('need arg to choice organization.')

    main(organization=args[1])
