from pyvesync import VeSync
from rich import print
from rich.logging import RichHandler
import collections
import getpass
import json
import logging
import os
import random
import requests
import sys
import time

logger = logging.getLogger(__name__)

upper_limit = 55
lower_limit = 40

# Documentation:
# https://github.com/webdjoe/pyvesync


class Humidifier:
    def __init__(self, veSyncHumid):
        self.hw = veSyncHumid
        self.hw.set_humidity_mode("manual")
        self.hw.turn_off()
        self.humidity = collections.deque([], maxlen=5)
        self.log_file = "/home/isaiah/vesync_log"
        self.is_on = False

    def run(self):
        while True:
            self.update()
            time.sleep(60 + (random.random() * 10 - 5))

    def set_display(self):
        if not self.hw.is_on:
            return

        hour = time.localtime().tm_hour
        display = self.hw.details["display"]

        if hour >= 8 and hour < 21:
            if not display:
                logger.info("Turning display on.")
                self.hw.turn_on_display()
        else:
            if self.hw.is_on and display:
                logger.info("Turning display off.")
                self.hw.turn_off_display()

    def update(self):
        self.hw.update()

        self.is_on = self.hw.is_on

        if self.hw.details["water_lacks"] or self.hw.details["water_tank_lifted"]:
            logger.warning(
                f"Tank issue. water_lacks: {self.hw.details['water_lacks']} water_tank_lifted: {self.hw.details['water_tank_lifted']}"
            )
            self.is_on = False

        self.humidity.append(self.hw.humidity)
        median = sorted(self.humidity)[len(self.humidity) // 2]

        if sys.stdout.isatty():
            logger.info(f"Active: {self.is_on} Humidity: {list(self.humidity)}")

        self.log()

        if self.hw.humidity < lower_limit and not self.is_on:
            if sys.stdout.isatty():
                logger.info("Turning humidifier on.")
            self.hw.set_mist_level(9)
            self.hw.turn_on()

        if median > upper_limit and self.is_on:
            if sys.stdout.isatty():
                logger.info("Turning humidifier off.")
            self.hw.turn_off()

        self.set_display()

    def log(self):
        try:
            r = requests.get("https://api.weather.gov/stations/KDCA/observations/latest")
            kdca = json.loads(r.text)
            h = kdca["properties"]["relativeHumidity"]["value"]
            t = kdca["properties"]["temperature"]["value"] * 9.0 / 5.0 + 32
        except:
            logger.exception("Failed to get weather from weather.gov")
            h = None
            t = None

        log_entry = {
            "humidifier.is_on": self.is_on,
            "indoor.humidity": self.hw.humidity,
            "outdoor.humidity": h,
            "outdoor.temp": t,
            "time.ctime": time.ctime(),
            "time.time": time.time(),
        }

        with open(self.log_file, "a") as f:
            json.dump(log_entry, f, indent=None)
            f.write("\n")


def main():
    password_file = "/home/isaiah/.config/vesync_password"
    if not os.path.exists(password_file):
        print("[bold red]VeSync password needed for Irgkenya4@gmail.com[/bold red]")
        if sys.stdout.isatty():
            with open(password_file, "w") as f:
                password = getpass.getpass()
                f.write(password)
        else:
            raise RuntimeError("Run script in TTY to set password")

    with open(password_file) as f:
        password = f.read()

    manager = VeSync("Irgkenya4@gmail.com", password)
    if not manager.login():
        os.unlink(password_file)
        raise RuntimeError("Login failed. Run again to set password")

    manager.update()
    assert manager.fans[0].device_name == "humidifier"
    humidifier = Humidifier(manager.fans[0])
    humidifier.run()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    main()
