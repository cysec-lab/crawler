from __future__ import annotations

import os
import sys
from datetime import datetime
from logging import getLogger
from multiprocessing import Process, Queue
from typing import Any, Optional

from crawler_init import crawler_host
from utils.logger import (log_listener_configure, log_listener_process,
                          worker_configurer)
from utils.sys_command import kill_chrome
from utils.save_result import dealing_after_fact, save_rod
from utils.sys_command import worker_configurer_sys_command

queue_log: Queue[Any] = Queue(-1)
logger = getLogger(__name__)


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
    worker_configurer_sys_command(queue_log)

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
        kill_chrome(process='geckodriver')
        kill_chrome(process='firefox-bin')

        logger.info('save used ROD before overwriting the ROD directory : START')
        save_rod(org_arg)
        logger.info('save used ROD before overwriting the ROD directory : DONE')

        logger.info('---dealing after fact---')
        dealing_after_fact(queue_log, org_arg)

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
