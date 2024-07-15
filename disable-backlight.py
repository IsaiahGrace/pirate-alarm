#! /usr/bin/env python

import gpiod
import gpiodevice

from gpiod.line import Direction, Value

output_low = gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE)
backlight = gpiodevice.get_pin(13, "backlight-ctrl", output_low)
