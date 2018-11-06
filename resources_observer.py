from threading import Thread
import psutil
from time import sleep
from sys_command import kill_chrome


# メモリ使用量がlimitを超えるとゾンビのヘッドレスブラウザをkillするスレッド
class MemoryObserverThread(Thread):
    def __init__(self, limit):
        super(MemoryObserverThread, self).__init__()
        self.limit = limit

    def run(self):
        while True:
            if psutil.virtual_memory().percent > self.limit:
                kill_chrome(process="geckodriver")
                kill_chrome(process='firefox')
            sleep(60)


# class ResourceObserverThread(Thread):
#     def __init__(self, ppid=None, cpu_limit=0, memory_limit=0, interval=1):
#         super(ResourceObserverThread, self).__init__()
#         self.cpu_limit = cpu_limit
#         self.mem_limit = memory_limit
#         self.ppid = ppid
#         self.cpu_num = cpu_count()
#         self.interval = interval
#
#     def run(self):
#         while True:
#             if self.ppid:
#                 family = get_family(self.ppid)
#             else:
#                 family = get_relate_browser_proc()
#
#             print("\n-----CPU-----")
#             ret = cpu_checker(family, limit=self.cpu_limit, cpu_num=self.cpu_num)
#             if ret:
#                 for p in ret:
#                     print("HIGH CPU PROCESS : {}".format(p.name()))
#
#             print("\n-----MEMORY-----")
#             ret = memory_checker(family, limit=self.mem_limit)
#             if ret:
#                 for p in ret:
#                     print("HIGH MEM PROCESS : {}".format(p.name()))
#
#             sleep(self.interval)


def memory_checker(family, limit):
    """
    rss
    122M 138K 624B
    14G 013M 640K 704B

    data
    1G 146M 949K 632
    15G 061M 020K 672

    uss
    31M 309K 824B
    13G 926M 871K 040B

    pss
    40M 269K 824
    13G 934M 951K 424B
    """
    ret = list()

    for p in family:
        mem_used = p.memory_full_info()[0]  # index: rss, vms, shared, text, lib, data, dirty, uss, pss, swap
        if mem_used > limit:
            ret.append({"proc": p, "mem_used": mem_used})
        print("Name : {}".format(p.name()))
        print("\tMEM : {} Mb".format(int(mem_used/1000000)))
    return ret


def cpu_checker(family, limit, cpu_num):
    ret = list()
    for p in family:
        cpu_per = p.cpu_percent(interval=0.05) / cpu_num
        if cpu_per > limit:
            ret.append({"proc": p, "cpu_per": cpu_per})
        print("Name : {}".format(p.name()))
        print("\tCPU %: {}".format(cpu_per))  # 788.7 を記録(約98% * 8core)
    return ret


def get_relate_browser_proc():
    res = list()
    p_list = [psutil.Process(p) for p in psutil.pids()]
    relate_browser = ["Web Content", "firefox", "geckodriver", "WebExtensions"]

    for p in p_list:
        if [p_name for p_name in relate_browser if p_name in p.name()]:
            res.append(p)
    return res


def get_family(ppid):
    family = list()
    family.extend(psutil.Process(ppid).children())
    i = 0
    while True:
        if len(family) == i:
            break
        proc = family[i]
        family.extend(proc.children())
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
    organization_path = os.path.dirname(os.path.abspath(__file__)) + "/../organization/"  # 絶対パス
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
