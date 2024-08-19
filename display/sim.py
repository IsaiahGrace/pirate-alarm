from PIL import Image
from rich import print
import logging
import pyray as rl
import queue
import threading
import os

logger = logging.getLogger(__name__)


class Screen:
    def __init__(self, **kwargs):
        logger.debug(f"Screen.__init__({kwargs})")
        self.screen_update_path = os.path.abspath("./screen-update.png")
        if os.path.exists(self.screen_update_path):
            try:
                os.remove(self.screen_update_path)
            except:
                pass
        self.update = threading.Event()
        self.stop = threading.Event()
        self.backlight = threading.Event()

        self.backlight.set()
        self.thread = threading.Thread(target=self.thread_main)
        self.thread.start()

    def close(self):
        self.stop.set()
        self.thread.join()

    def stopped(self):
        return self.stop.is_set()

    def display(self, image):
        logger.debug(f"Screen.display({image})")
        assert isinstance(image, Image.Image)
        image.save(self.screen_update_path, format="png")
        self.update.set()

    def set_backlight(self, enabled):
        logger.debug(f"Screen.set_backlight({enabled})")
        if enabled:
            self.backlight.set()
        else:
            self.backlight.clear()
        self.update.set()

    def thread_main(self):
        try:
            self.main_loop()
        finally:
            self.stop.set()

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

        while not self.stop.is_set() and not rl.window_should_close():
            # Update the screen if we have a new frame to display
            if self.update.is_set():
                self.update.clear()
                if os.path.exists(self.screen_update_path):
                    update_image = rl.load_image(self.screen_update_path)
                    rl.image_draw(screen_image, update_image, screen_rect, screen_rect, rl.WHITE)

                # Either draw the screen, or a black square if the backlight is off
                if self.backlight.is_set():
                    rl.image_draw(window_image, screen_image, screen_rect, window_screen_rect, rl.WHITE)
                else:
                    rl.image_draw_rectangle_rec(window_image, window_screen_rect, rl.BLACK)

                rl.unload_texture(window_texture)
                window_texture = rl.load_texture_from_image(window_image)

            rl.begin_drawing()
            rl.draw_texture(window_texture, 0, 0, rl.WHITE)
            rl.end_drawing()

        rl.close_window()
        self.stop.set()
