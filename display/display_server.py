from PIL import Image  # , ImageDraw
from rich import print
from rich.logging import RichHandler
import json
import logging
import os
import platform
import time
import zmq
import threading

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

    def display(self, image):
        self.screen.display(image)

    def set_backlight(self, enabled):
        logger.debug(f"Display.set_backlight({enabled})")
        self.screen.set_backlight(enabled)


class Compositor:
    def __init__(self, display):
        self.display = display
        self.backlight = threading.Event()
        self.active_icons = dict()
        self.icon_bar_color = (0, 0, 0, 255)

    def __enter__(self):
        self.thread = threading.Thread(target=self.thread_main)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def stopped(self):
        return display.stopped()

    def draw_icon(self, icon):
        pass

    def clear_icon(self, icon):
        pass

    def icon_bar_color(self, r, g, b, a):
        pass

    def backlight_tread(self):
        pass

    def draw_image(self, image_path):
        logger.debug(f"Display.draw_image('{image_path}')")
        with Image.open(image_path) as image:
            if image.width != WIDTH or image.height != HEIGHT:
                image = image.resize((WIDTH, HEIGHT))
                logger.debug(f"Image resized from ({image.width},{image.height}) to ({WIDTH},{HEIGHT})")
            self.display.draw_image(image)


class Server:
    def __init__(self, compositor):
        self.compositor = compositor
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.backlight = False
        self.backlight_timeout = time.time()

        self.commands_schema = {
            "clear_icon": (self.cmd_clear_icon, {"icon": str}),
            "draw_icon": (self.cmd_draw_icon, {"icon": str}),
            "icon_bar_color": (self.cmd_icon_bar_color, {"r": int, "g": int, "b": int, "a": int}),
            "draw_image": (self.cmd_draw_image, {"relative_path": str}),
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
        return self.compositor.stopped()

    def run(self):
        while not self.stopped():
            if self.socket.poll(1000):
                self.handle_message(self.socket.recv())

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
        self.compositor.draw_icon(cmd["icon"])

    def cmd_clear_icon(self, cmd):
        self.compositor.clear_icon(cmd["icon"])

    def cmd_draw_image(self, cmd):
        image = os.path.abspath(cmd["relative_path"])
        assert os.path.exists(image)
        self.display.draw_image(image)

    def cmd_icon_bar_color(self, cmd):
        self.compositor.icon_bar_color(cmd["r"], cmd["g"], cmd["b"], cmd["a"])


def main():
    logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])
    with Display() as display:
        with Compositor(display) as compositor:
            with Server(compositor) as server:
                server.run()


if __name__ == "__main__":
    main()
