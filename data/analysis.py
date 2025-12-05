from rich import print
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sys
import time


def main(args):
    def read_file(path):
        with open(path) as f:
            for line in f.readlines():
                record = json.loads(line)
                record["humidifier.is_on"] = 50 if record["humidifier.is_on"] else 40
                yield record

    data = pd.DataFrame.from_records(read_file(args[0]))
    print(data)

    start = data["time.time"][0]
    end = data["time.time"].iloc[-1]

    fig, ax = plt.subplots()
    plt.xlim(start, end)
    ax.xaxis.set_major_formatter(lambda x, _: time.ctime(x))
    ax.plot([start, end], [40, 40], "k")
    ax.plot([start, end], [50, 50], "k")
    ax.plot(data["time.time"], data["indoor.humidity"])
    ax.plot(data["time.time"], data["outdoor.humidity"])
    ax.plot(data["time.time"], data["outdoor.temp"])
    ax.plot(data["time.time"], data["humidifier.is_on"], ".")

    plt.show()


if __name__ == "__main__":
    main(sys.argv[1:])
