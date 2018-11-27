from threading import Thread
import psutil
from time import sleep
from sys_command import kill_chrome
from location import location


# メモリ使用量がlimitを超えるとゾンビのヘッドレスブラウザをkillするスレッド
# だったが、60秒感覚でppidが1のブラウザをkillするスレッドに
class MemoryObserverThread(Thread):
    def __init__(self, limit=0):
        super(MemoryObserverThread, self).__init__()
        self.limit = limit

    def run(self):
        proc_name = ["geckodriver", "firefox"]
        while True:
            # if psutil.virtual_memory().percent > self.limit:
            # kill_chrome(process="geckodriver")
            # kill_chrome(process='firefox')
            kill_process_cand = get_relate_browser_proc(proc_name)
            for proc in kill_process_cand:
                try:
                    if proc.ppid() == 1:
                        print("kill {}".format(proc))
                        kill_process_list = get_family(proc.pid)
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


def memory_checker(family, limit):
    ret = list()
    ret2 = list()

    for p in family:
        try:
            mem_used = p.memory_full_info()[0]  # index: rss, vms, shared, text, lib, data, dirty, uss, pss, swap
            mem_used = int(mem_used/1000000)    # translate to Mb
        except Exception as e:
            # print(location() + str(e), flush=True)
            pass
        else:
            if mem_used > limit:
                try:
                    ret.append({"p_name": p.name(), "mem_used": mem_used})
                except psutil._exceptions.NoSuchProcess:
                    pass
                except Exception as e:
                    # print(location() + str(e), flush=True)
                    pass
            ret2.append(mem_used)
    return ret, ret2


def cpu_checker(family, limit, cpu_num):
    ret = list()
    ret2 = list()
    for p in family:
        try:
            cpu_per = p.cpu_percent(interval=0.5) / cpu_num
        except Exception as e:
            # print(location() + str(e), flush=True)
            pass
        else:
            if cpu_per > limit:
                try:
                    ret.append({"p_name": p.name(), "cpu_per": cpu_per})
                except psutil._exceptions.NoSuchProcess:
                    pass
                except Exception as e:
                    # print(location() + str(e), flush=True)
                    pass
            ret2.append(cpu_per)
    return ret, ret2


def get_relate_browser_proc(proc_name):
    # proc_name = ["Web Content", "firefox", "geckodriver", "WebExtensions"]
    res = list()
    proc_list = list()
    try:
        pid_list = psutil.pids()
    except psutil._exceptions.NoSuchProcess:
        return res
    except Exception as e:
        print(location() + str(e), flush=True)
        return res
    for pid in pid_list:
        try:
            proc_list.append(psutil.Process(pid))
        except psutil._exceptions.NoSuchProcess:
            pass
        except Exception as e:
            print(location() + str(e), flush=True)

    for p in proc_list:
        try:
            if [p_name for p_name in proc_name if p_name in p.name()]:
                res.append(p)
        except Exception:
            pass
    return res


def get_family(ppid):
    family = list()
    try:
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
                # print(location() + str(e), flush=True)
                pass
                del family[i]
            else:
                i += 1
        family.reverse()  # 子プロセス順にする (killするときに親を最初にkillしたくないので)
    return family


def main():
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
    mem_per = psutil.virtual_memory().percent
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
