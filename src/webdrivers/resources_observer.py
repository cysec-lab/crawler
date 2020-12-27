from __future__ import annotations

from logging import getLogger
from multiprocessing import Queue
from threading import Thread
from time import sleep
from typing import Any, Dict, List, Set, Tuple, Union

import psutil
from utils.logger import worker_configurer

logger = getLogger(__name__)


class MemoryObserverThread(Thread):
    """
    60秒間隔でppidが1のブラウザをkillするスレッドに
    """
    def __init__(self, queue_log: Queue[Any], ctx: Dict[str, Any], limit: int=0):
        worker_configurer(queue_log, logger)
        super(MemoryObserverThread, self).__init__()
        self.ctx = ctx
        self.limit = limit

    def run(self):
        logger.debug("Start memory observer thread")
        # proc_name: Set[str] = set(["geckodriver", "firefox-bin"])
        proc_name: Set[str] = set(["firefox-bin"])
        while not self.ctx["stop"]:
            time = 0
            while time < 60:
                # 60秒待機する
                if self.ctx["stop"]:
                    break
                sleep(0.5)
                time += 0.5

            logger.debug("memory observer thread wakeup to work")
            kill_process_cand = get_relate_browser_proc(proc_name)

            for proc in kill_process_cand:
                kill_process_list: List[psutil.Process] = list()
                try:
                    if proc.ppid() == 1:
                        logger.debug(f"kill target proc: {proc}")
                        kill_process_list = get_family(proc.pid) # type: ignore
                        kill_process_list.append(proc)
                except Exception as err:
                    logger.exception(f'{err}')
                    pass
                if kill_process_list:
                    for kill_proc in kill_process_list:
                        try:
                            kill_proc.kill()
                            logger.debug("killed: {}".format(kill_proc))
                        except Exception as err:
                            logger.exception(f'{err}')
        logger.debug("memory observer thread Finish")


def memory_checker(family: list[psutil.Process], limit: int)->Tuple[list[Dict[str, Union[str, int]]], list[int]]:
    """
    メモリ使用率を調査する

    return:
        ret: 各プロセスについてLimitをこえた場合にプロセス名と使用率を返す
        ret2: 各プロセスの使用率を返す
    """
    ret: list[Dict[str, Union[str, int]]] = list()
    ret2: list[int] = list()

    logger.debug("Memory checker called.")

    for p in family:
        try:
            mem_used: float = p.memory_full_info()[0]  # index: rss, vms, shared, text, lib, data, dirty, uss, pss, swap
            mem_used = int(mem_used/1000000)    # translate to Mb
            p_name = p.name()
        except psutil.NoSuchProcess:
            # 外でプロセスファミリーを取ったときに存在したけどいまは死んでるなら発生
            pass
        except Exception as err:
            logger.exception(f'Memory Check: {err}')
            pass
        else:
            if mem_used > limit:
                ret.append({"p_name": p_name, "mem_used": mem_used})
            ret2.append(mem_used)
    return ret, ret2


def cpu_checker(family: list[psutil.Process], limit: float, cpu_num: float)->Tuple[list[Dict[str, Union[str, float]]], list[float]]:
    """
    cpu使用率を調査する

    return:
        ret: 各プロセスについてLimitをこえた場合にプロセス名と使用率を返す
        ret2: 各プロセスの使用率を返す
    """
    ret: list[Dict[str, Union[str, float]]] = list()
    ret2: list[float] = list()
    for p in family:
        try:
            # TODO: interval(指定秒数遅延発生)してるから消していい？
            # TODO: cpu_num で割るともともと全体のコア数で割ってるものを更に割ってない？
            # cpu_per = p.cpu_percent(interval=0.9) / cpu_num
            cpu_per = p.cpu_percent() / cpu_num
            p_name = p.name()
        except psutil.NoSuchProcess:
            # 外でプロセスファミリーを取ったときに存在したけどいまは死んでるなら発生
            pass
        except Exception as err:
            logger.exception(f'{err}')
            pass
        else:
            if cpu_per > limit:
                ret.append({"p_name": p_name, "cpu_per": cpu_per})
            ret2.append(cpu_per)
    return ret, ret2


def get_relate_browser_proc(proc_name: Set[str])->list[psutil.Process]:
    """
    現在のpidリストを取得する
    各pidのプロセス名を proc_list に格納
    proc_name() に含まれるかつ現在のpidに存在するプロセスをリストで返す
    """
    res: List[psutil.Process] = list()

    try:
        for proc in psutil.process_iter():
            if proc.name() in proc_name:
                res.append(proc)
    except psutil.NoSuchProcess:
        logger.info('No process alive')
    except Exception as err:
        logger.exception(f'{err}')
        print(f'{err}')

    return res


def get_family(ppid: int) -> list[psutil.Process]:
    family: list[psutil.Process] = list()
    try:
        # Family に現在のPPIDの子プロセスを再帰的に探索して全部入れる
        family.extend(psutil.Process(ppid).children(recursive=True))
        # 子プロセスを先にする(Killするときに親から殺さないために)
        family.reverse()
    except Exception as err:
        logger.exception(f'Exception: {err}')
    return family


def main():
    """
    実行中クローラを /ROD/<>/running.tmp の存在で確認
    現在のメモリ使用量(全体)を調べて50%超えているならなんとリブートするから注意
    """
    import os
    from datetime import datetime
    now_dir = os.path.dirname(os.path.abspath(__file__))  # ファイル位置(src)を絶対パスで取得
    os.chdir(now_dir)

    reboot_flag = True

    start_time = datetime.now().strftime('%Y/%m/%d, %H:%M:%S')
    logger.info("Check RAM percent at %s", start_time)

    # 実行中のクローラがあるか
    organization_path = now_dir + "/../organization/"  # 絶対パス
    org_dirs = os.listdir(organization_path)
    for org_dir in org_dirs:
        if os.path.isdir(organization_path + "/" + org_dir):
            if os.path.exists(organization_path + "/" + org_dir + "/running.tmp"):
                logger.info("TODO: %s is running...")
                reboot_flag = False

    # メモリ使用量確認
    mem_per: float = psutil.virtual_memory().percent
    logger.info("TODO: Used RAM percent is %f%", mem_per)

    # クローラが実行されていないのに、メモリを50%使っているのはおかしいので再起動
    # compizなどのGUI関連のプロセスがずっと起動しているとメモリを食っていく。原因は不明。
    if reboot_flag and (mem_per > 50):
        logger.warning("Reboot")
        from utils.sys_command import reboot
        reboot()


if __name__ == '__main__':
    main()
