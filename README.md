# MicroPython SH1107 display driver

This module provides a MicroPython driver for the SH1107 display controller. It is mainly based on the [SH1106 driver](https://github.com/robert-hh/SH1106) made by @robert-hh and others. It includes some extensions and improvements including a link to the `large_text` method in the MicroPython FrameBuffer extension [framebuf2](https://github.com/peter-l5/framebuf2). 

## Features

All the methods of MicroPython FrameBuffer in the [framebuf](https://docs.micropython.org/en/v1.18/library/framebuf.html "MicroPython v1.18 documentation") module are accessible as at MicroPython v1.18. The `polygon` method and other changes included in version 1.19.1 are not yet implemented. 

## Interfaces

The code includes an I2C interface. An SPI interface is also included but this is broken at present.

## Requirements

This code has been tested on a Raspberry Pi Pico with MicroPython version 1.18.
