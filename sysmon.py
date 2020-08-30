"""
Report / log computer utilization

Usage: 'python sysmon.py [log]'

If 'log' is not passed, no logging will occur.
"""

import curses
import logging
import psutil
import signal
import sys
import threading
import time

NONE = 1
CRITICAL = 2
WARNING = 3
GOOD = 4
INFO = 5

FILE = "sysmon.log"
FORMAT = '%(asctime)s %(levelname)-8s %(message)s'
logger = None
do_log = False
if "log" in sys.argv:
    do_log = True
    with open(FILE, "w") as fp:
        fp.write("")
    logging.basicConfig(
        level=logging.INFO,
        format=FORMAT,
        filename=FILE)
    logger = logging.getLogger('sysmon')

def bytes_h(n: int) -> (int, str):
    # convert n to a unit postfix
    if n >= 1000000.0:
        return n / 1000000.0, "MB"
    elif n >= 1000.0:
        return n / 1000.0, "KB"
    else:
        return n, "B"

class Screen():
    def __init__(self):
        self.stdscr = curses.initscr()
        self.stdscr.clear()
        curses.cbreak()
        curses.noecho()
        curses.start_color()
        self.height, self.width = self.stdscr.getmaxyx()
        self.done = False

        curses.init_pair(CRITICAL, curses.COLOR_WHITE, curses.COLOR_RED)
        curses.init_pair(WARNING, curses.COLOR_WHITE, curses.COLOR_YELLOW)
        curses.init_pair(GOOD, curses.COLOR_WHITE, curses.COLOR_GREEN)
        curses.init_pair(INFO, curses.COLOR_WHITE, curses.COLOR_BLUE)

    def __del__(self):
        curses.endwin()

    def putstr(self, s: str, x: int, y: int, color: int=NONE):
        self.stdscr.move(y, x)
        if color is NONE:
            self.stdscr.addstr(s)
        else:
            self.stdscr.addstr(s, curses.color_pair(color))

    def update(self) -> bool:
        self.stdscr.refresh()
        curses.doupdate()

def control(s: Screen):
    while True:
        ch = s.stdscr.getch()
        if ch == 27: # ESC
            s.done = True
            evt.set()
            return

sent: int = 0
received: int = 0
sent_last: int
received_last: int
line: int
level: int
builder: str

s = Screen()
threading.Thread(target=control, args=(s,)).start()
evt = threading.Event() # pause the while loop until 'control' finishes or timeout is reached

while not s.done:
    if do_log: builder = ""
    tmp: str
    line = 1
    call = logger.info

    s.putstr("===== Sysmon ====", 1, line, INFO)
    line += 1

    cpu_percent_it = psutil.cpu_percent(percpu=True)
    it = range(psutil.cpu_count())

    for i, cpu in zip(it, cpu_percent_it):
        if cpu > 80:
            level = CRITICAL
            call = logger.critical
        elif cpu > 60:
            level = WARNING
            call = logger.warning
        else:
            level = GOOD

        tmp = "{:.2f}%".format(i, cpu)
        s.putstr("CORE_{}: ".format(i), 1, line, NONE)
        s.putstr(f"{tmp}\n", 9, line, level)
        if do_log: builder = f"{builder} CORE_{i}: {tmp}"
        line += 1
    
    avg = sum(cpu_percent_it) / len(cpu_percent_it)
    if avg > 80:
        level = CRITICAL
        call = logger.critical
    elif avg > 60:
        level = WARNING
        call = logger.warning
    else:
        level = GOOD

    tmp = "{:.2f}%".format(avg)
    s.putstr("TOTAL: ", 1, line, NONE)
    s.putstr(f"{tmp}\n", 9, line, level)
    if do_log: builder = f"{builder} TOTAL: {tmp}"
    line += 2

    network = psutil.net_io_counters()
    sent_last = sent
    received_last = received
    sent = network[0]
    received = network[1]

    send_size, send_unit = bytes_h(sent - sent_last)
    recv_size, recv_unit = bytes_h(received - received_last)

    tmp = "SEND: {:.2f}{}".format(send_size, send_unit)
    s.putstr(f"{tmp}\n", 1, line, NONE)
    if do_log: builder = f"{builder} {tmp}"
    line += 1

    tmp = "RECV: {:.2f}{}".format(recv_size, recv_unit)
    s.putstr(f"{tmp}\n", 1, line, NONE)
    if do_log: builder = f"{builder} {tmp}"
    call(builder)
    line += 2
    s.putstr("ESC to cancel...", 1, line, INFO)

    s.update()
    evt.wait(timeout=5)
