from rich import print
import logging
import os
import PIL
import pyray as rl
import threading
import zmq
import zmqNet

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
        self.update_done = threading.Event()
        self.stop = threading.Event()
        self.backlight = threading.Event()

        self.backlight.set()
        self.thread = threading.Thread(target=self.thread_main)
        self.thread.start()

        self.zmq_context = zmq.Context()
        self.zmq_socket = self.zmq_context.socket(zmq.PUB)
        self.zmq_socket.bind(zmqNet.RAYLIB_SIM_BUTTON_PUB)

    def close(self):
        self.stop.set()
        self.thread.join()

    def stopped(self):
        return self.stop.is_set()

    def display(self, image):
        assert isinstance(image, PIL.Image.Image)
        image.save(self.screen_update_path, format="png")
        self.update_done.clear()
        self.update.set()
        if not self.update_done.wait(1):
            self.stop.set()

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

    def handle_click(self, x, y):
        size = (40, 94)
        A = (278, 35)
        B = (278, 181)
        X = (588, 35)
        Y = (588, 181)
        clicked = None
        rect = None

        if x >= A[0] and x <= A[0] + size[0] and y >= A[1] and y <= A[1] + size[1]:
            clicked = "A"
            rect = rl.Rectangle(A[0], A[1], size[0], size[1])

        if x >= B[0] and x <= B[0] + size[0] and y >= B[1] and y <= B[1] + size[1]:
            clicked = "B"
            rect = rl.Rectangle(B[0], B[1], size[0], size[1])

        if x >= X[0] and x <= X[0] + size[0] and y >= X[1] and y <= X[1] + size[1]:
            clicked = "X"
            rect = rl.Rectangle(X[0], X[1], size[0], size[1])

        if x >= Y[0] and x <= Y[0] + size[0] and y >= Y[1] and y <= Y[1] + size[1]:
            clicked = "Y"
            rect = rl.Rectangle(Y[0], Y[1], size[0], size[1])

        if clicked is not None:
            logger.info(clicked)
            self.zmq_socket.send(clicked.encode("utf-8"))

        return rect

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
        click = None
        while not self.stop.is_set() and not rl.window_should_close():
            if rl.is_mouse_button_pressed(rl.MOUSE_BUTTON_LEFT):
                if not click:
                    pos = rl.get_mouse_position()
                    click = self.handle_click(pos.x, pos.y)
            elif click:
                click = None

            # Update the screen if we have a new frame to display
            if self.update.is_set():
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
                self.update.clear()
                self.update_done.set()

            rl.begin_drawing()
            rl.draw_texture(window_texture, 0, 0, rl.WHITE)
            if click:
                rl.draw_rectangle_rec(click, rl.Color(26, 28, 32, 255))
            rl.end_drawing()

        rl.close_window()
        self.stop.set()
