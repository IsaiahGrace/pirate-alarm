from PIL import Image
from rich import print
from rich.logging import RichHandler
import json
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
ICON_BAR_HEIGHT = 48


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

        self.commands_schema = {
            "draw_icon": (self.cmd_draw_icon, {"icon": str}),
            "draw_image": (self.cmd_draw_image, {"relative_path": str}),
            "draw_icon_bar": (self.cmd_draw_icon_bar, {"r": int, "g": int, "b": int, "a": int}),
        }

    def __enter__(self):
        logger.debug("Starting zmq display server.")
        self.socket.bind("tcp://*:5555")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def parse(self, command):
        cmd = json.loads(command)
        if "command" not in cmd:
            raise ValueError(f"message does not contain a command")
        for field, expected_type in self.commands_schema[cmd["command"]][1].items():
            if field not in cmd:
                raise ValueError(f'"{cmd["command"]}" does not contain required field: "{field}"')
            if not isinstance(cmd[field], expected_type):
                raise ValueError(f'{cmd["command"]}["{field}"] must be "{type}" not "{type(cmd[field])}"')
        return cmd

    def respond_error(self, exception):
        self.socket.send(
            str.encode(
                json.dumps(
                    {
                        "response": "exception",
                        "name": type(exception).__name__,
                        "text": str(exception),
                    }
                )
            )
        )

    def respond_ok(self):
        self.socket.send(str.encode(json.dumps({"response": "ok"})))

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
                if self.socket.poll(1000):
                    self.handle_message(self.socket.recv())
            except Exception as e:
                logger.exception("Display server main loop")

    def handle_message(self, message):
        logger.info(message)
        try:
            cmd = self.parse(message)
            command = cmd["command"]
            self.commands_schema[command][0](cmd)
        except Exception as e:
            logger.exception("Display server message handler")
            self.respond_error(e)
        else:
            self.respond_ok()

    def cmd_draw_icon(self, cmd):
        icon = os.path.abspath(cmd["icon"])
        self.set_backlight(True)
        icon_bar = os.path.abspath("../images/icon_bar_black.png")
        self.display.draw_image_path(icon_bar)
        self.display.draw_image_path(icon)

    def cmd_draw_image(self, cmd):
        icon = os.path.abspath(cmd["relative_path"])
        self.set_backlight(True)
        self.display.draw_image_path(icon)

    def cmd_draw_icon_bar(self, cmd):
        raise NotImplementedError("Sorry, not yet!")


def main():
    logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])
    with Display() as display:
        with Server(display) as server:
            server.run()


if __name__ == "__main__":
    main()
