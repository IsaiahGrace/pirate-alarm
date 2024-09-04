from PIL import Image, ImageColor
from rich import print
from rich.logging import RichHandler
import json
import logging
import os
import threading
import time
import zmq
import zmqNet

logger = logging.getLogger(__name__)


class ButtonClient:
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(zmqNet.BUTTON_SUB)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")

    def get_button_event(self):
        msg = self.socket.recv().decode()
        return msg


def log_button_events():
    button_client = ButtonClient()
    while True:
        event = button_client.get_button_event()
        logger.info(event)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])
    log_button_events()
