# MicroPython SH1107 display driver - with large fonts

This module provides a MicroPython driver for the SH1107 display controller. It is mainly based on the [SH1106 driver](https://github.com/robert-hh/SH1106) made by @robert-hh and others. It includes some extensions and improvements including a link to the `large_text` method in the MicroPython FrameBuffer extension [framebuf2](https://github.com/peter-l5/framebuf2). 

## Version

This is a beta version, and whilst working includes some development/testing code.

## Usage

The sh1107.py module code and framebuf2.py module code should be uploaded to the Raspberry Pico Pi (or other Microcontroller running MicroPython. Example use:
```
    from machine import Pin, I2C
    import sh1107

    i2c0 = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
    display = sh1107.SH1107_I2C(128, 128, i2c0, Pin(16), address=0x3d, rotate=90)
    display.sleep(False)
    display.fill(0)
    display.text('SH1107', 0, 0, 1)
    display.text('driver', 0, 8, 1)
    display.show()
```

## Features

All the methods of MicroPython FrameBuffer in the [framebuf](https://docs.micropython.org/en/v1.18/library/framebuf.html "MicroPython v1.18 documentation") module are accessible as at MicroPython v1.18. The `polygon` method and other changes included in version 1.19.1 are not yet implemented. 

## Interfaces

The code includes an I2C interface. An SPI interface is also included but this is broken at present.

## Requirements

This code has been tested on a Raspberry Pi Pico with MicroPython version 1.18.
