from rich import print
import logging
import pyray as rl
import queue
import threading

logger = logging.getLogger(__name__)


class Vec2:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Screen:
    def __init__(self, **kwargs):
        logger.debug(f"Screen.__init__({kwargs})")

        self.frames = queue.Queue()
        self.stop = threading.Event()
        self.backlight = threading.Event()

        self.backlight.set()
        self.thread = threading.Thread(target=self.main_loop)
        self.thread.start()

    def close(self):
        self.stop.set()
        self.thread.join()

    def stopped(self):
        return self.stop.is_set()

    def display(self, image):
        logger.debug(f"Screen.display({image})")
        self.frames.put(image)

    def set_backlight(self, enabled):
        logger.debug(f"Screen.set_backlight({enabled})")
        if enabled:
            self.backlight.set()
        else:
            self.backlight.clear()

    def main_loop(self):
        rl.set_config_flags(rl.FLAG_WINDOW_TRANSPARENT)
        rl.init_window(700, 343, "pirate-alarm simulator")
        rl.set_target_fps(60)
        rl.set_window_state(rl.FLAG_WINDOW_UNDECORATED)
        rl.clear_background(rl.BLANK)

        window_image = rl.gen_image_color(700, 343, rl.BLANK)
        screen_image = rl.gen_image_color(240, 240, rl.BLACK)

        screen_rect = rl.Rectangle(0, 0, 240, 240)
        window_rect = rl.Rectangle(0, 0, 700, 343)
        window_screen_rect = rl.Rectangle(331, 29, 240, 240)

        background = rl.load_image("../images/Pirate_Audio_DAC.png")
        rl.image_draw(window_image, background, window_rect, window_rect, rl.WHITE)
        window_texture = rl.load_texture_from_image(window_image)

        backlight_status = self.backlight.is_set()
        update = False

        while not self.stop.is_set() and not rl.window_should_close():
            # Update the screen if we have a new frame to display
            if not self.frames.empty():
                frame = self.frames.get()
                logger.debug(f'Drawing image: "{frame.filename}"')
                image = rl.load_image(frame.filename)
                rl.image_draw(screen_image, image, screen_rect, screen_rect, rl.WHITE)
                update = True

            # Either draw the screen, or a black square if the backlight is off
            if self.backlight.is_set():
                rl.image_draw(window_image, screen_image, screen_rect, window_screen_rect, rl.WHITE)
            else:
                rl.image_draw_rectangle_rec(window_image, window_screen_rect, rl.BLACK)

            if backlight_status != self.backlight.is_set():
                backlight_status = self.backlight.is_set()
                update = True

            if update:
                rl.unload_texture(window_texture)
                window_texture = rl.load_texture_from_image(window_image)
                update = False

            rl.begin_drawing()
            rl.draw_texture(window_texture, 0, 0, rl.WHITE)
            rl.end_drawing()

        rl.close_window()
        self.stop.set()
