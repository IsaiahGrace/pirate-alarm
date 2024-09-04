from rich import print
from rich.logging import RichHandler
import logging
import zmq
import zmqNet

logger = logging.getLogger(__name__)


class ButtonEvents:
    def __init__(self, callback_A, callback_B, callback_X, callback_Y):
        self.callback_A = callback_A
        self.callback_B = callback_B
        self.callback_X = callback_X
        self.callback_Y = callback_Y

    def __enter__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(zmqNet.RAYLIB_SIM_BUTTON_SUB)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")
        return self

    def run(self):
        while True:
            msg = self.socket.recv().decode()
            if msg == "A":
                self.callback_A()
            if msg == "B":
                self.callback_B()
            if msg == "X":
                self.callback_X()
            if msg == "Y":
                self.callback_Y()

    def __exit__(self, exc_type, exc_value, traceback):
        self.socket.disconnect(zmqNet.RAYLIB_SIM_BUTTON_SUB)
