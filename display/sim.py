import logging

logger = logging.getLogger(__name__)


class Screen:
    def __init__(self, **kwargs):
        logger.debug(f"Screen.__init__({kwargs})")

    def display(self, image):
        logger.debug(f"Screen.display({image})")

    def set_backlight(self, enabled):
        logger.debug(f"Screen.set_backlight({enabled})")
