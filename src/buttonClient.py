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


def log_button_events():
    pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])
    log_button_events()
