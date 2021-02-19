from __future__ import annotations

from multiprocessing import Queue, Process
from time import sleep
from typing import Union, Dict, Any

def finish_thread(dict: Dict[str, Union[Queue[str], Process]]) -> bool:
    """
    指定されたキューに 'end' を流して指定されたプロセスを終了させる
    clamd_scan や summarize_alert がこれで終了させられる

    bool: 正常終了できた場合にはtrue, terminate した場合にはFalse
    """
    queue: Queue[Any] = dict['recv']
    process: Process = dict['process']

    queue.put('end')
    process.join(timeout=60.0)
    if process.is_alive():
        # 終わるまで待機
        process.terminate()
        sleep(1)
        return False
    return True