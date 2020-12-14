from __future__ import annotations

import datetime
import logging
import logging.handlers
import os
from collections.abc import Callable
from multiprocessing import Queue
from typing import Any

console_format = '%(levelname)-8s %(process)6d %(processName)-12s: <%(name)s, %(lineno)d> %(message)s'
file_format    = '%(asctime)s %(levelname)-8s %(process)6d %(processName)-12s: <%(name)s, %(lineno)d> %(message)s'

loglevel = logging.DEBUG

def log_listener_configure(path: str):
    """
    Log受信機の作成
    /log/%Y%m%d-%H%M%S.log と 標準出力に出力する

    args:
        path: srcへのパス
    """
    root = logging.getLogger()
    ch = logging.StreamHandler()
    ch.setLevel(loglevel)
    format_console = logging.Formatter(console_format)
    ch.setFormatter(format_console)
    root.addHandler(ch)

    # Logファイル名の作成
    base_path = path[0:path.rfind('/')]
    time_now = datetime.datetime.now()
    if not os.path.exists(base_path + '/log'):
        os.mkdir(base_path + '/log')
    log_file = base_path + '/log/' + time_now.strftime('%Y%m%d-%H%M') + '.log'

    # Logファイルを作成
    fh = logging.handlers.RotatingFileHandler(log_file, maxBytes=2000000000, backupCount=100000)
    fh.setLevel(loglevel)
    format_file = logging.Formatter(file_format)
    fh.setFormatter(format_file)
    root.addHandler(fh)

def log_listener_process(path: str, queue: Queue[Any], configurer: Callable[[str], None]):
    """
    Loggerの出力を受け取り続けるトップレベルループ
    ここでログを集約して出力する

    Args:
        path: ログファイルを置く場所
        queue: ログを流すキュー
        configurer: 設定を行う関数(log_listener_configure)
    """
    configurer(path)
    while True:
        try:
            record = queue.get()
            if record is None:  # We send this as a sentinel to tell the listener to quit.
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)  # No level or filter logic applied - just do it!
        except Exception:
            import sys
            import traceback
            print('logger.py: Exception occured!', file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

def worker_configurer(queue: Queue[Any]):
    """
    各プロセスに対して実行される
    1つのログにまとめるために配置されたプロセスからキューに向けてログを流す

    args:
        queue: ログを流すキュー
    """
    h = logging.handlers.QueueHandler(queue)
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(logging.DEBUG)
