import subprocess
import sys

if __name__ == '__main__':
    length = len(sys.argv)

    if length != 2:
        sys.exit('Usage: system.py <command> [start|stop|restart] ')

    command = sys.argv[1]

    if command == 'start':
        subprocess.call(["siuu", "start"])
    elif command == 'stop':
        subprocess.call(["siuu", "stop"])
    elif command == 'restart':
        subprocess.call(["siuu", ])
