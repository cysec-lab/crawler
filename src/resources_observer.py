from threading import Thread
import psutil
from time import sleep
from location import location
from typing import Tuple, Dict, Union


# だったが、60秒感覚でppidが1のブラウザをkillするスレッドに
class MemoryObserverThread(Thread):
    def __init__(self, limit: int=0):
        super(MemoryObserverThread, self).__init__()
        self.limit = limit

    def run(self): # type: ignore
        """
        TODO オーバライドしていいのここ？？
        """
        proc_name: list[str] = ["geckodriver", "firefox"]
        while True:
            # if psutil.virtual_memory().percent > self.limit:
            # kill_chrome(process="geckodriver")
            # kill_chrome(process='firefox')
            kill_process_cand = get_relate_browser_proc(proc_name)
            for proc in kill_process_cand:
                try:
                    if proc.ppid() == 1:
                        print("kill {}".format(proc))
                        kill_process_list = get_family(proc.pid) # type: ignore
                        kill_process_list.append(proc)
                        for killed_proc in kill_process_list:
                            try:
                                killed_proc.kill()
                                print("\t{}".format(killed_proc))
                            except Exception as e:
                                print(location() + str(e), flush=True)
                    # else:
                    #     print("else {}".format(proc))
                    #     print("\tppid ={}, parent name ={}".format(proc.ppid(), psutil.Process(proc.ppid()).name()))
                except Exception:
                    pass
            sleep(60)


def memory_checker(family: list[psutil.Process], limit: int)->Tuple[list[Dict[str, Union[str, int]]], list[int]]:
    """
    メモリ使用率を調査する

    return:
        ret: 各プロセスについてLimitをこえた場合にプロセス名と使用率を返す
        ret2: 各プロセスの使用率を返す
    """
    ret: list[Dict[str, Union[str, int]]] = list()
    ret2: list[int] = list()

    for p in family:
        try:
            mem_used: float = p.memory_full_info()[0]  # index: rss, vms, shared, text, lib, data, dirty, uss, pss, swap
            mem_used = int(mem_used/1000000)    # translate to Mb
            p_name = p.name()
        except psutil.NoSuchProcess:
            # 外でプロセスファミリーを取ったときに存在したけどいまは死んでるなら発生
            pass
        except Exception as e:
            print(location() + str(e), flush=True)
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
        except Exception as e:
            print(location() + str(e), flush=True)
            pass
        else:
            if cpu_per > limit:
                ret.append({"p_name": p_name, "cpu_per": cpu_per})
            ret2.append(cpu_per)
    return ret, ret2


def get_relate_browser_proc(proc_name: list[str])->list[psutil.Process]:
    """
    現在のpidリストを取得する
    各pidのプロセス名を proc_list に格納
    proc_name() に含まれるかつ現在のpidに存在するプロセスをリストで返す
    """
    # proc_name = ["Web Content", "firefox", "geckodriver", "WebExtensions"]
    res: list[psutil.Process] = list()
    proc_list: list[psutil.Process] = list()
    try:
        pid_list = psutil.pids()
    except psutil.NoSuchProcess:
        return res
    except Exception as e:
        # TODO エラーハンドリング
        print(location() + str(e), flush=True)
        return res

    for pid in pid_list:
        try:
            proc_list.append(psutil.Process(pid))
        except psutil.NoSuchProcess:
            pass
        except Exception as e:
            print(location() + str(e), flush=True)

    for p in proc_list:
        # 与えられたproc_nameの中に上で取ったproc_listに含まれるnameがあった場合追加
        if [p_name for p_name in proc_name if p_name in p.name()]:
            res.append(p)
    return res


def get_family(ppid: int) -> list[psutil.Process]:
    family: list[psutil.Process] = list()
    try:
        # >>> Process(ppid)
        # sample: psutil.Process(pid=15511, name='python', status='running', started='17:14:47')
        # >>> Process(ppid).children()
        # [] (list)
        family.extend(psutil.Process(ppid).children())
    except Exception as e:
        # print(location() + str(e), flush=True)
        pass
    else:
        i = 0
        while True:
            if len(family) <= i:
                break
            proc = family[i]
            try:
                family.extend(proc.children())
            except Exception as e:
                print('resources_observer.py: ' + location() + str(e), flush=True)
                pass
                del family[i]
            else:
                i += 1
        family.reverse()  # 子プロセス順にする (killするときに親を最初にkillしたくないので)
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
    print("Check RAM percent at {}".format(start_time))

    # 実行中のクローラがあるか
    organization_path = now_dir + "/../organization/"  # 絶対パス
    org_dirs = os.listdir(organization_path)
    for org_dir in org_dirs:
        if os.path.isdir(organization_path + "/" + org_dir):
            if os.path.exists(organization_path + "/" + org_dir + "/running.tmp"):
                print("{} is running.".format(org_dir))
                reboot_flag = False

    # メモリ使用量確認
    mem_per: float = psutil.virtual_memory().percent
    print("Used RAM percent is {}%.".format(mem_per))

    # クローラが実行されていないのに、メモリを50%使っているのはおかしいので再起動
    # compizなどのGUI関連のプロセスがずっと起動しているとメモリを食っていく。原因は不明。
    if reboot_flag and (mem_per > 50):
        print("reboot\n")
        from sys_command import reboot
        reboot()
    print("\n")


if __name__ == '__main__':
    main()
