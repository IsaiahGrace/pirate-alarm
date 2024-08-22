from rich import print
from rich.logging import RichHandler
import json
import logging
import os
import platform
import threading
import time
import zmq
import zmqNet

logger = logging.getLogger(__name__)

# Import either the LCD screen or a raylib simulation of the screen
machine = platform.machine()
if machine == "x86_64" or machine == "AMD64":
    from buttonRaylib import ButtonEvents
else:
    from buttonRaylib import ButtonEvents


class ButtonServer:
    def __init__(self):
        pass

    def run(self):
        with ButtonEvents(
            self.on_press_A,
            self.on_press_B,
            self.on_press_X,
            self.on_press_Y,
        ) as buttons:
            buttons.run()

    def on_press_A(self):
        pass

    def on_press_B(self):
        pass

    def on_press_X(self):
        pass

    def on_press_Y(self):
        pass


def main():
    pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])
    main()
