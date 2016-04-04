# /usr/bin/env/python

"""
Make logs colored. Original script at https://gist.github.com/obensonne/2629510
"""

import errno
import sys
import signal
import re


# terminal color codes for specific log levels
CC_DEBUG = '\033[37m'  # gray
CC_INFO = '\033[32m'  # green
CC_WARNING = '\033[35m'  # purple
CC_ERROR = '\033[31m'  # red
CC_END = '\033[0m'

# mapping patterns for input lines to color codes
color_map = (
    (re.compile(r'^.*?ERROR'), CC_ERROR),
    (re.compile(r'^.*?(warn|WARNING)'), CC_WARNING),
    (re.compile(r'^.*?info'), CC_INFO),
    (re.compile(r'^.*?DEBUG'), CC_DEBUG),
)


def print_colored(color, line):
    print('%s%s%s' % (color, line, CC_END))


def pipe():
    """ Continuously read lines from stdin and print them colored """
    last_color = CC_ERROR
    while True:
        try:
            line = sys.stdin.readline()
        except IOError as e:
            if e.errno != errno.EINTR:
                print('abort: %s' % e)
            break
        if not line:
            break
        line = line[:-1]
        for rx, color in color_map:
            if rx.match(line):
                print_colored(color, line)
                last_color = color
                break
        else:
            print_colored(last_color, line)


def main():
    if len(sys.argv) > 1:
        print('colog colorizes log lines from stdin')
        sys.exit(1)
    signal.signal(signal.SIGINT, lambda *args: None)
    pipe()


if __name__ == '__main__':
    main()
