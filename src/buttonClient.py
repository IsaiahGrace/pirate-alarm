from rich import print
from rich.logging import RichHandler
import logging
import zmq
import zmqNet

logger = logging.getLogger(__name__)


class ButtonClient:
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(zmqNet.BUTTON_SUB)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")

    def get_button_event(self, blocking=True):
        flags = 0 if blocking else zmq.NOBLOCK
        try:
            return self.socket.recv(flags=flags).decode()
        except zmq.error.Again:
            return None


def log_button_events():
    button_client = ButtonClient()
    while True:
        event = button_client.get_button_event()
        logger.info(event)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    log_button_events()
