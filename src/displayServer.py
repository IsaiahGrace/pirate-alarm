from PIL import Image, ImageColor
from rich import print
from rich.logging import RichHandler
import json
import logging
import os
import platform
import threading
import time
import zmq
import zmqNet

# Import either the LCD screen or a raylib simulation of the screen
machine = platform.machine()
if machine == "x86_64" or machine == "AMD64":
    import screenSim

    SCREEN_BACKEND = screenSim.Screen
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
BACKLIGHT_TIMEOUT = 300


class Display:
    def __init__(self):
        self.screen = SCREEN_BACKEND(
            height=HEIGHT,
            width=WIDTH,
            rotation=270,
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


class Color:
    def __init__(self, r, g, b, a):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def __str__(self):
        r = max(0, min(255, int(self.r)))
        g = max(0, min(255, int(self.g)))
        b = max(0, min(255, int(self.b)))
        a = max(0, min(255, int(self.a)))
        return f"#{r:02x}{g:02x}{b:02x}{a:02x}"


class Compositor:
    def __init__(self, display):
        self.display = display
        self.backlight = threading.Event()
        self.stop = threading.Event()
        self.active_icons = dict()
        self.icon_bar_color = Color(86, 142, 215, 200)
        self.icon_mask = Image.open(os.path.abspath("../images/icon_bar_mask.png"))
        self.icon_bar = Image.new("RGBA", (WIDTH, HEIGHT))
        self.background = Image.new("RGBA", (WIDTH, HEIGHT))

    def __enter__(self):
        self.thread = threading.Thread(target=self.thread_main)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop.set()
        self.thread.join()

    def stopped(self):
        if self.display.stopped() or self.stop.is_set():
            self.stop.set()
            return True
        else:
            return False

    def thread_main(self):
        try:
            self.backlight_tread()
        finally:
            self.stop.set()

    def backlight_tread(self):
        last_update_time = time.time()
        backlight_status = True
        while not self.stopped():
            if self.backlight.wait(1.0):
                if not backlight_status:
                    self.display.set_backlight(True)
                last_update_time = time.time()
                backlight_status = True
                self.backlight.clear()

            if backlight_status and time.time() - last_update_time >= BACKLIGHT_TIMEOUT:
                self.display.set_backlight(False)
                backlight_status = False

    def draw_icon(self, category, symbol):
        self.active_icons[category] = symbol
        self.redraw_icons()

    def clear_icon(self, category, symbol):
        del self.active_icons[category]
        self.redraw_icons()

    def icon_bar_color(self, r, g, b, a):
        self.icon_bar_color.r = r
        self.icon_bar_color.g = g
        self.icon_bar_color.b = b
        self.icon_bar_color.a = a
        self.redraw_icons()

    def redraw_icons(self):
        icon_bar_bg = Image.new("RGBA", (WIDTH, HEIGHT), str(self.icon_bar_color))
        self.icon_bar = Image.new("RGBA", (WIDTH, HEIGHT))
        self.icon_bar.paste(icon_bar_bg, mask=self.icon_mask)
        for category, symbol in self.active_icons.items():
            path = os.path.abspath(f"../images/icon_{category}_{symbol}.png")
            with Image.open(path) as icon_image:
                self.icon_bar.paste(icon_image, mask=icon_image)
        self.redraw()

    def draw_image(self, image_path):
        logger.debug(f"Compositor.draw_image('{image_path}')")
        with Image.open(image_path) as new_image:
            if new_image.width != WIDTH or new_image.height != HEIGHT:
                new_image = new_image.resize((WIDTH, HEIGHT))
                logger.debug(f"Image resized from ({new_image.width},{new_image.height}) to ({WIDTH},{HEIGHT})")
            self.background.paste(new_image)
        self.redraw()

    def redraw(self):
        self.backlight.set()
        self.display.display(Image.alpha_composite(self.background, self.icon_bar))


class Server:
    def __init__(self, compositor):
        self.compositor = compositor
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)

        self.commands_schema = {
            "clear_icon": (self.cmd_clear_icon, {"icon": str}),
            "draw_icon": (self.cmd_draw_icon, {"icon": str}),
            "icon_bar_color": (self.cmd_icon_bar_color, {"r": int, "g": int, "b": int, "a": int}),
            "draw_image": (self.cmd_draw_image, {"relative_path": str}),
        }
        self.icon_types = {
            "alarm": {"check", "none", "note", "off", "plus"},
            "wifi": {"connected", "disconnected", "wait"},
        }

    def __enter__(self):
        logger.debug("Starting zmq display server.")
        self.socket.bind(zmqNet.DISPLAY_CLIENT_FILTER)
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
            logger.exception("Server message handler")
            self.respond_error(e)
        else:
            self.respond_ok()

    def cmd_draw_icon(self, cmd):
        category, symbol = cmd["icon"].split("_")
        assert symbol in self.icon_types[category]
        self.compositor.draw_icon(category, symbol)

    def cmd_clear_icon(self, cmd):
        category, symbol = cmd["icon"].split("_")
        assert symbol in self.icon_types[category]
        self.compositor.clear_icon(category, symbol)

    def cmd_draw_image(self, cmd):
        image = os.path.abspath(cmd["relative_path"])
        assert os.path.exists(image)
        self.compositor.draw_image(image)

    def cmd_icon_bar_color(self, cmd):
        self.compositor.icon_bar_color(cmd["r"], cmd["g"], cmd["b"], cmd["a"])


def main():
    with Display() as display:
        with Compositor(display) as compositor:
            with Server(compositor) as server:
                server.run()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    main()
