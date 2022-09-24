# MicroPython SH1107 display driver - with large fonts

This module provides a MicroPython driver for the SH1107 display controller. It is mainly based on the [SH1106 driver](https://github.com/robert-hh/SH1106) made by @robert-hh and others. It supports both I2C and SPI interfaces. It includes some extensions and improvements including:
- a link to the `large_text` method in the MicroPython FrameBuffer extension [framebuf2](https://github.com/peter-l5/framebuf2)
- addition of a `set_start_line` method for some scrolling functionality
- optimised screen updating when the screen is rotated at 90 or 270 degrees
- some slight speed improvements

## Version

This is a production version (v216).

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

## Interfaces and tested displays 

The code includes both I2C and SPI interfaces. 

It has been tested with a Raspberry Pi Pico two 128x128 displays, as follows:
- [Adafruit 1.12 inch OLED](https://www.adafruit.com/product/5297 "Adafruit 1.12 inch OLED") (I2C interface) (at 3.3 volts)
- [Pimoroni 1.12 inch OLED](https://shop.pimoroni.com/products/1-12-oled-breakout?variant=12628508704851 "Pimoroni 1.12 inch OLED") (SPI version) (works best with 5V supply)

Changes to some constants will be needed for 128x64 displays. See annotations in the code.

## Requirements

This code has been tested with MicroPython version 1.18.

## Release notes

#### Version 216

Changes include:
- code tidied up
- annotations added for register values that would need changing for 128x64 displays

#### Version 210

Changes include:
- added `set_start_line()` function which implements scrolling in one direction (whether x or y depends on display orientation)
- added `_SET_DISPLAY_OFFSET` constant and included display offset command in start-up sequence. The offset value may need editing for displays smalled than 128x128
- added 100ms sleep after power on command. This is recommended in the SH1107 datasheet and should reduce the risk of EIO interface errors
- added page address = 0 command to start up sequence. This improves reliability of start-up

