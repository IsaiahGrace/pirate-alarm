#! /usr/bin/env python

import gpiod
import gpiodevice

from gpiod.line import Direction, Value


def set_backlight(enabled):
    output_value = Value.ACTIVE if enabled else Value.INACTIVE
    output = gpiod.LineSettings(direction=Direction.OUTPUT, output_value=output_value)
    backlight = gpiodevice.get_pin(13, "backlight-ctrl", output)


if __name__ == "__main__":
    set_backlight(False)
