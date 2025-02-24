import os
import subprocess
import sys

if __name__ == '__main__':
    try:
        length = len(sys.argv)

        if length != 2:
            sys.exit('Usage: system.py <command> [start|stop|restart] ')

        home = os.environ['HOME']
        exe = f'{home}/.siuu/siuu'
        command = sys.argv[1]
        env = os.environ.copy()

        if command == 'start':
            subprocess.call([exe, "start"])
        elif command == 'stop':
            subprocess.call([exe, "stop"])
        elif command == 'restart':
            subprocess.call([exe, "restart"])
        else:
            sys.exit('Invalid command. Usage: start|stop|restart')
        print(command, end=None)
    except Exception as e:
        print(f"Error occurred: {e}")
