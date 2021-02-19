from __future__ import annotations

from multiprocessing import Queue
from time import sleep
from typing import Any, Dict, Tuple, Union


def send_to_parent(sendq: Queue[Union[str, Dict[str, Any], Tuple[str, ...]]], data: Union[str, Dict[str, Any], Tuple[str, ...]]):
    """
    各サーバを回るcrawler_main()プロセスが
    親プロセス(main.py)に自身が担当しているサイトのURLを要求する
    親からのデータは q_recv に入れられる
    """
    if not sendq.full():
        sendq.put(data)  # 親にdataを送信
    else:
        sleep(1)
        sendq.put(data)

