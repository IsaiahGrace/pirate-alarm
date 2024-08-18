#!/usr/bin/env python3
from PIL import Image
from rich import print
from rich.logging import RichHandler
import logging
import os
import platform
import socket
import time

# Import either the LCD screen or a raylib simulation of the screen
if platform.machine() == "aarch64":
    import st7789

    SCREEN_SIM = False
    SCREEN_BACKEND = st7789.ST7789
    SCREEN_CS = st7789.BG_SPI_CS_FRONT
else:
    import sim

    SCREEN_SIM = True
    SCREEN_BACKEND = sim.Screen
    SCREEN_CS = None


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
        pass

    def run(self):
        logger.debug("Starting zmq display server.")


def internet(host="8.8.8.8", port=53, timeout=3):
    """
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        logger.warn(ex)
        return False


def startup(display):
    logger.debug("Displaying startup screens")
    display.draw_image("WiFi_none.bmp")
    while not internet():
        display.draw_image("WiFi_wait.bmp")
        time.sleep(1)
        display.draw_image("WiFi_none.bmp")
        time.sleep(1)
    display.draw_image("WiFi_connected.bmp")
    time.sleep(2)


def main():
    logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])
    logger.debug(f'platform.machine() = "{platform.machine()}"')
    with Display() as display:
        display.set_backlight(True)
        startup(display)
        display.set_backlight(False)
        server = Server(display)
        server.run()


if __name__ == "__main__":
    main()
