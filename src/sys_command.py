import os
import subprocess


# 子プロセスを返す
def return_children(my_pid):
    try:
        children = subprocess.check_output(['ps', '--ppid', str(my_pid), '--no-heading', '-o', 'pid'])
    except subprocess.CalledProcessError:
        return list()
    else:
        child_list = children.decode().replace(' ', '').split('\n')
        try:
            child_list.remove('')
        except ValueError:
            pass
        return child_list


# meより下の家族プロセスkillする
def kill_family(me):
    family = list()
    family.append(me)
    i = 0
    while True:
        if len(family) == i:
            break
        pid_ = family[i]
        family.extend(return_children(pid_))
        i += 1
    family.reverse()
    print("kill {}'s {}".format(me, family))
    for kill_pid in family:
        try:
            os.system("kill -9 " + kill_pid)
        except Exception as e:
            print("kill error : {}".format(e))
        else:
            print('kill {}'.format(kill_pid))


# ppidのプロセスがupstartなら、そのchrome(driver)は孤児
# ppidが1だったら、そのchrome(driver)は孤児
def check_upstart(proc_ppid):
    if proc_ppid == '1':
        return True
    try:
        ps = subprocess.Popen(['ps', '--no-header', '--pid', proc_ppid], stdout=subprocess.PIPE)
        awk = subprocess.Popen(['awk', "{print $4}"], stdin=ps.stdout, stdout=subprocess.PIPE)
        upstart = awk.stdout
    except subprocess.CalledProcessError:
        return False
    else:
        for upstart_b in upstart:
            upstart_s = upstart_b.decode().strip()
            if 'upstart' == upstart_s:
                return True
            else:
                return False


def kill_chrome(process):
    try:
        # zombie_chrome_list = subprocess.check_output(['ps', '-f', '-C', 'google-chrome-stable', '--ppid', '1', '|',
        #                                               'grep', 'google-chrome-stable', '|', 'awk', "'{print $2}"])
        ps = subprocess.Popen(['ps', '-f', '-C', process, '--no-header'], stdout=subprocess.PIPE)
        awk = subprocess.Popen(['awk', "{print $2, $3}"], stdin=ps.stdout, stdout=subprocess.PIPE)
        proc_list = awk.stdout
    except subprocess.CalledProcessError:
        print('No chrome')
        return 0
    else:
        for driver in proc_list:
            pid_ppid = driver.decode().rstrip().split(' ')
            print('{} : {}'.format(process, pid_ppid))
            if check_upstart(pid_ppid[1]):
                kill_family(pid_ppid[0])


def reboot():
    subprocess.call("reboot")
