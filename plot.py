"""
Plot the data logged from sysmon.

Usage: 'python plot.py [net]'

If 'net' is not passed, CPU utilization will be displayed instead
"""

from datetime import datetime
from matplotlib import pyplot as plt
import matplotlib
import sys

plot_network = "net" in sys.argv
plot_cpu = not plot_network
COL_DATE = 0
COL_TIME = 1
COL_CPU = 12
COL_SEND = 14
COL_RECV = 16

def units_g(n: str) -> float:
    # return kilobytes/units given a string that ends in
    # B KB or MB and the front is a number
    if n.endswith("MB"):
        return float(n[:-2]) * 1000.0
    elif n.endswith("KB"):
        return float(n[:-2])
    elif n.endswith("%"):
        return float(n[:-1])
    else: # n[-1] == "B"
        return float(n[:-1]) / 1000.0

def time_to_dt(d: str, t: str) -> datetime:
    fmt = "%Y-%m-%d %H:%M:%S"
    return datetime.strptime(f"{d} {t[:t.index(',')]}", fmt)

logfile = open("sysmon.log", "r")
x = []
y = []

if plot_network:
    r = []
    for line in logfile.readlines():
        split = line.split()
        x.append(time_to_dt(split[COL_DATE], split[COL_TIME]))
        y.append(units_g(split[COL_SEND]))
        r.append(units_g(split[COL_RECV]))

    # 0th items are incorrect
    del x[0]
    del y[0]
    del r[0]

    print("Cumulative Sent: {:.2f}KB".format(sum(y)))
    print("Cumulative Recv: {:.2f}KB".format(sum(r)))

    dates = matplotlib.dates.date2num(x)
    sends, = plt.plot_date(dates, y, linestyle="solid", color="blue")
    recvs, = plt.plot_date(dates, r, linestyle="solid", color="red")
    plt.title("Kilobytes Sent / Received")
    plt.legend([sends, recvs], ["Sent", "Received"])
    plt.ylabel("Kilobytes (KB)")
    plt.show()

else:
    for line in logfile.readlines():
        split = line.split()
        x.append(time_to_dt(split[COL_DATE], split[COL_TIME]))
        y.append(units_g(split[COL_CPU]))
    dates = matplotlib.dates.date2num(x)
    utilization, = plt.plot_date(dates, y, linestyle="solid")
    plt.title("CPU Utilization")
    plt.legend([utilization], "Utilization")
    plt.ylabel("Percent (%)")
    plt.show()
