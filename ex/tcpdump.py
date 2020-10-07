

import subprocess


def tcpdump_main():
    p = subprocess.Popen(('sudo', 'tcpdump', '-l', 'host 10.0.2.15'), stdout=subprocess.PIPE)
    for row in iter(p.stdout.readline, b''): # type: ignore
        print(row.rstrip())


if __name__ == '__main__':
    tcpdump_main()
