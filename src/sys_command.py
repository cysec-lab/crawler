from __future__ import annotations

import subprocess
from logging import getLogger
from multiprocessing import Queue
from typing import Any, Iterable, List

from utils.logger import worker_configurer

logger = getLogger(__name__)

def return_children(my_pid: str) -> List[str]:
    """
    子プロセスを返す
    """
    try:
        children = subprocess.check_output(['ps', '--ppid', str(my_pid), '--no-heading', '-o', 'pid'])
    except subprocess.CalledProcessError:
        return list()
    else:
        child_list: list[str] = children.decode().replace(' ', '').split('\n')
        try:
            child_list.remove('')
        except ValueError:
            pass
        return child_list


def kill_family(me: str):
    """
    meより下の家族プロセスkillする
    """
    family: list[str] = list()
    family.append(me)
    i = 0
    while True:
        if len(family) == i:
            break
        pid_ = family[i]
        family.extend(return_children(pid_))
        i += 1
    family.reverse()
    logger.info("kill %s's %s", me, family)
    for kill_pid in family:
        try:
            subprocess.check_call(['kill', '-9', str(kill_pid)], stderr=subprocess.DEVNULL)
        except Exception as err:
            logger.exception(f'Process kill error: {err}')
        else:
            logger.debug('Process kill: %s', kill_pid)


def check_upstart(proc_ppid: str):
    """
    ppidのプロセスがupstartなら、そのchrome(driver)は孤児
    ppidが1だったら、そのchrome(driver)は孤児
    """
    if proc_ppid == '1':
        return True
    try:
        ps = subprocess.Popen(['ps', '--no-header', '--pid', proc_ppid], stdout=subprocess.PIPE)
        awk = subprocess.Popen(['awk', "{print $4}"], stdin=ps.stdout, stdout=subprocess.PIPE)
        upstart: Iterable[Any] = awk.stdout # type: ignore
    except subprocess.CalledProcessError:
        return False
    else:
        for upstart_b in upstart:
            upstart_s = upstart_b.decode().strip()
            if 'upstart' == upstart_s:
                return True
            else:
                return False


def kill_chrome(queue_log: Queue[Any], process: str):
    worker_configurer(queue_log, logger)
    try:
        # zombie_chrome_list = subprocess.check_output(['ps', '-f', '-C', 'google-chrome-stable', '--ppid', '1', '|',
        #                                               'grep', 'google-chrome-stable', '|', 'awk', "'{print $2}"])
        ps = subprocess.Popen(['ps', '-f', '-C', process, '--no-header'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        awk = subprocess.Popen(['awk', "{print $2, $3}"], stdin=ps.stdout, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ps.stdout.close()
        proc_list: Iterable[Any] = awk.stdout # type: ignore
    except subprocess.CalledProcessError:
        logger.warning('No Chrome process')
        return 0
    except Exception as err:
        logger.exception(f'{err}')
    else:
        for driver in proc_list:
            pid_ppid = driver.decode().rstrip().split(' ')
            logger.info('Process: %s -> %s', process, str(pid_ppid))
            if check_upstart(pid_ppid[1]):
                kill_family(pid_ppid[0])


def reboot():
    subprocess.call("reboot")
