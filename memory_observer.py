from threading import Thread
from psutil import virtual_memory
from time import sleep
from sys_command import kill_chrome


# メモリ使用量がlimitを超えるとゾンビのヘッドレスブラウザをkillするスレッド
class MemoryObserverThread(Thread):
    def __init__(self, limit):
        super(MemoryObserverThread, self).__init__()
        self.limit = limit

    def run(self):
        while True:
            if virtual_memory().percent > self.limit:
                kill_chrome(process="geckodriver")
                kill_chrome(process='firefox')
            sleep(60)


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
    mem_per = virtual_memory().percent
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
