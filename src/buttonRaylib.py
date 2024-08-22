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


class ButtonEvents:
    def __init__(
        self,
        callback_A,
        callback_B,
        callback_X,
        callback_Y,
    ):
        pass
