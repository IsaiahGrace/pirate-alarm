#! /usr/bin/env python

from dataclasses import dataclass
from rich import print
from rich.logging import RichHandler
import buttonClient
import displayClient
import logging
import os
import subprocess
import sys
import random

logger = logging.getLogger(__name__)


@dataclass
class Config:
    image: str = "../images/cat.jpg"
    sound: str = "../sounds/chirp.mp3"
    snooze_min: int = 5
    snooze_reps: int = 3


alarm_types = {
    "sunday": Config(),
    "workday": Config(),
}

for t in alarm_types.values():
    assert os.path.exists(t.image)
    assert os.path.exists(t.sound)


class Alarm:
    def __init__(self, alarm_name):
        self.display = displayClient.DisplayClient()
        self.display.connect()
        self.config = alarm_types[alarm_name]
        self.buttons = buttonClient.ButtonClient()

    def trigger(self):
        logger.info("Alarm triggered")
        if os.path.isdir(self.config.image):
            self.display.draw_image(
                self.config.image
                + "/"
                + random.choice(
                    list(filter(lambda i: i.endswith(".png"), os.listdir(self.config.image))),
                ),
            )
        else:
            self.display.draw_image(self.config.image)
        play = subprocess.Popen(["play", "--no-show-progress", self.config.sound])

        while play.poll() is None:
            button = self.buttons.get_button_event(blocking=False)
            if button in ("A", "B"):
                self.snooze()
                play.kill()
            elif button in ("X", "Y"):
                play.kill()

    def snooze(self):
        logger.info("Alarm snoozed")
        subprocess.run(
            [
                "systemd-run",
                f"--on-active={self.config.snooze_min * 60}",
                "--unit",
                "irg-alarm@workday.service",
            ]
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    assert sys.argv[1] in alarm_types
    alarm = Alarm(sys.argv[1])
    alarm.trigger()
