from __future__ import annotations

import os
from multiprocessing import Queue, Process
from logging import getLogger
from datetime import datetime
from typing import Any
from utils.logger import log_listener_configure, log_listener_process, worker_configurer
from utils.save_result import save_rod, dealing_after_fact

if __name__ == "__main__":
    """
    save_result を実行すると終了処理を全部やってくれる
    なぜか最後の処理だけされないことが多発したため作った
    """

    organization = "ritsumeikan"

    queue_log: Queue[Any] = Queue(-1)
    now_dir =  os.path.dirname(os.path.abspath(__file__))
    os.chdir(now_dir)
    log_listener = Process(target=log_listener_process,
                    args=(now_dir, queue_log, log_listener_configure))
    log_listener.start()
    worker_configurer(queue_log)
    logger = getLogger(__name__)

    organization_path = organization_path = now_dir[0:now_dir.rfind('/')] + '/organization/' + organization
    print(organization_path)
    # result_historyディレクトリがなければ作成
    if not os.path.exists(organization_path + '/result_history'):
        os.mkdir(organization_path + '/result_history')
    dir_name = str(len(os.listdir(organization_path + '/result_history')) + 1)

    org_arg = {'result_no': dir_name, 'org_path': organization_path}

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

    # 実行中であることを示すファイルを削除する
    if os.path.exists(organization_path + '/running.tmp'):
        os.remove(organization_path + '/running.tmp')

    # Logを集めるリスナーを終了させる
    queue_log.put_nowait(None)
    log_listener.join()