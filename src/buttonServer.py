from rich import print
from rich.logging import RichHandler
import logging
import platform
import zmq
import zmqNet
import displayClient

logger = logging.getLogger(__name__)

# Import either the LCD screen or a raylib simulation of the screen
machine = platform.machine()
if machine == "x86_64" or machine == "AMD64":
    from buttonRaylib import ButtonEvents
else:
    from buttonGpio import ButtonEvents


class ButtonServer:
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(zmqNet.BUTTON_PUB)
        self.display = displayClient.DisplayClient()
        self.display.connect()

    def run(self):
        with ButtonEvents(
            self.on_press_A,
            self.on_press_B,
            self.on_press_X,
            self.on_press_Y,
        ) as buttons:
            buttons.run()

    def on_press_A(self):
        logger.info("A button pressed!")
        self.socket.send("A".encode("utf-8"))
        self.display.backlight()

    def on_press_B(self):
        logger.info("B button pressed!")
        self.socket.send("B".encode("utf-8"))
        self.display.backlight()

    def on_press_X(self):
        logger.info("X button pressed!")
        self.socket.send("X".encode("utf-8"))
        self.display.backlight()

    def on_press_Y(self):
        logger.info("Y button pressed!")
        self.socket.send("Y".encode("utf-8"))
        self.display.backlight()


def main():
    button_server = ButtonServer()
    button_server.run()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    main()
