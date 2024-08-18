import pyray as pr
import logging
import threading
import queue

logger = logging.getLogger(__name__)


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
        pr.init_window(240, 240, "pirate-alarm")
        pr.set_target_fps(60)

        pr.begin_drawing()
        pr.clear_background(pr.RAYWHITE)
        pr.end_drawing()

        textures = dict()

        while not self.stop.is_set() and not pr.window_should_close():
            pr.begin_drawing()
            if not self.frames.empty():
                image = self.frames.get()
                logger.debug(f'Drawing image: "{image.filename}"')
                if image.filename not in textures:
                    textures[image.filename] = pr.load_texture(image.filename)
                pr.draw_texture(textures[image.filename], 0, 0, pr.WHITE)

            if not self.backlight.is_set():
                pr.clear_background(pr.BLACK)

            pr.end_drawing()
        pr.close_window()
