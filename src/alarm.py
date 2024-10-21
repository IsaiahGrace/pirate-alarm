#! /usr/bin/env python

from dataclasses import dataclass
from rich import print
from rich.logging import RichHandler
import displayClient
import logging
import os
import subprocess
import sys

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

    def trigger(self):
        self.display.draw_image(self.config.image)
        subprocess.run(["play", "--no-show-progress", self.config.sound])


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    assert sys.argv[1] in alarm_types
    alarm = Alarm(sys.argv[1])
    alarm.trigger()
