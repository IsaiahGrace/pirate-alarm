#!/usr/bin/env python3
from PIL import Image
from rich import print
from rich.logging import RichHandler
import logging
import os
import platform

# Import either the LCD screen or a raylib simulation of the screen
if platform.machine() == "aarch64":
    import st7789

    SCREEN_BACKEND = st7789.ST7789
    SCREEN_CS = st7789.BG_SPI_CS_FRONT
else:
    import sim

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

    def draw_image(self, image_path):
        logger.debug(f"Display.draw_image({image_path})")
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


def main():
    logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])
    logger.debug(f'platform.machine() = "{platform.machine()}"')
    display = Display()
    display.set_backlight(False)
    display.draw_image("../images/bmp/WiFi_connected.bmp")


if __name__ == "__main__":
    main()
