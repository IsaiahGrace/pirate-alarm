#!/usr/bin/env python3
from PIL import Image
from rich import print
from rich.logging import RichHandler
import logging
import os
import platform
import time
import zmq

# Import either the LCD screen or a raylib simulation of the screen
machine = platform.machine()
if machine == "x86_64" or machine == "AMD64":
    import sim

    SCREEN_BACKEND = sim.Screen
    SCREEN_CS = None
    SCREEN_SIM = True
else:
    import st7789

    SCREEN_BACKEND = st7789.ST7789
    SCREEN_CS = st7789.BG_SPI_CS_FRONT
    SCREEN_SIM = False

logger = logging.getLogger(__name__)

# Display properties
HEIGHT = 240
WIDTH = 240


class Display:
    def __init__(self):
        self.screen = SCREEN_BACKEND(
            height=HEIGHT,
            width=WIDTH,
            rotation=0,  # TODO: Ensure this is correct
            port=0,
            cs=SCREEN_CS,
            dc=9,
            backlight=13,
            spi_speed_hz=80 * 1000 * 1000,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if SCREEN_SIM:
            self.screen.close()

    def stopped(self):
        if SCREEN_SIM:
            return self.screen.stopped()
        else:
            return False

    def draw_image(self, image_name):
        return self.draw_image_path(os.path.abspath(f"../images/{image_name}"))

    def draw_image_path(self, image_path):
        logger.debug(f"Display.draw_image('{image_path}')")
        with Image.open(image_path) as image:
            if image.width != WIDTH or image.height != HEIGHT:
                image = image.resize((WIDTH, HEIGHT))
                logger.debug(f"Image resized from ({image.width},{image.height}) to ({WIDTH},{HEIGHT})")
            self.screen.display(image)

    def set_backlight(self, enabled):
        logger.debug(f"Display.set_backlight({enabled})")
        self.screen.set_backlight(enabled)


class Server:
    def __init__(self, display):
        self.display = display
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.backlight = False
        self.backlight_timeout = time.time()

    def __enter__(self):
        logger.debug("Starting zmq display server.")
        self.socket.bind("tcp://*:5555")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def stopped(self):
        return self.display.stopped()

    def set_backlight(self, enabled):
        self.display.set_backlight(enabled)
        self.backlight = enabled
        if enabled:
            self.backlight_timeout = time.time()

    def run(self):
        self.set_backlight(False)
        while not self.stopped():
            if self.backlight and time.time() - self.backlight_timeout > 300:
                self.set_backlight(False)

            try:
                self.handle_message()
            except Exception as e:
                logger.error(e)

    def handle_message(self):
        if self.socket.poll(1000):
            message = self.socket.recv()
            logger.info(f"Received draw request for {message}")
            path = os.path.abspath(message)
            if not os.path.exists(path):
                self.socket.send(b"File not found")
            else:
                self.set_backlight(True)
                self.display.draw_image_path(path)
                self.socket.send(b"Done")


def main():
    logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])
    with Display() as display:
        with Server(display) as server:
            server.run()


if __name__ == "__main__":
    main()
