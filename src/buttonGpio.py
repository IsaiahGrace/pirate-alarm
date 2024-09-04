from rich import print
import datetime
import gpiod
import logging

logger = logging.getLogger(__name__)

buttons = {
    "A": 5,
    "B": 6,
    "X": 16,
    "Y": 24,
}

pins = {
    5: "A",
    6: "B",
    16: "X",
    24: "Y",
}

for b, p in buttons.items():
    assert pins[p] == b

for p, b in pins.items():
    assert buttons[b] == p


class ButtonEvents:
    def __init__(self, callback_A, callback_B, callback_X, callback_Y):
        self.callbacks = {
            buttons["A"]: callback_A,
            buttons["B"]: callback_B,
            buttons["X"]: callback_X,
            buttons["Y"]: callback_Y,
        }

    def __enter__(self):
        settings = gpiod.LineSettings(
            direction=gpiod.line.Direction.INPUT,
            edge_detection=gpiod.line.Edge.FALLING,
            debounce_period=datetime.timedelta(milliseconds=1),
        )
        self.lines = gpiod.request_lines(
            "/dev/gpiochip0",
            consumer="irg-button-server",
            config={
                buttons["A"]: settings,
                buttons["B"]: settings,
                buttons["X"]: settings,
                buttons["Y"]: settings,
            },
        ).__enter__()
        return self

    def run(self):
        logger.info("Waiting on gpio events...")
        while True:
            if self.lines.wait_edge_events():
                for event in self.lines.read_edge_events():
                    self.callbacks[event.line_offset]()
            else:
                logger.warning("wait_edge_events() returned False")

    def __exit__(self, exc_type, exc_value, traceback):
        self.lines.__exit__(exc_type, exc_value, traceback)
