# MicroPython SH1107 display driver - with large fonts

This module provides a MicroPython driver for OLED displays with the SH1107 controller IC. It is mainly based on the [SH1106 driver](https://github.com/robert-hh/SH1106) made by @robert-hh and others. The driver supports 128x128 pixel displays with I2C or SPI interfaces. It may need some parameters amending for 128x64 displays. (See: [supported displays](#supported-displays).) 

## Features

This driver offers **screen rotation**: the screen can be initialised at 0, 90, 180 or 270 degrees rotation. The rotation can be changed by 180 degrees after initialisation, but not by 90 degrees clock-wise or anti-clockwise. This is because 90 and 270 degrees use a different framebuffer mode and screen updating method which are set on initialisation. In these orientations the screen updates are a bit slower.

The driver builds in the facility to use the **`large_text()`** method in the MicroPython FrameBuffer extension [framebuf2](https://github.com/peter-l5/framebuf2). Moreover, some limited **hardware scrolling** functionality can be used with the `display_start_line()` method.

With an I2C connection at 400,000 bps a 128x128 display will achieve about 16 frames per second when orientated at 0 or 180 degrees and 10 frames per second at 90 or 270 degrees. Partial updates are faster, for example, 1 row of text can be updated in around 5 milliseconds (tested values using a Raspberry Pi pico at standard clock speed). 

## Usage

The [sh1107.py module code](/sh1107.py) should be uploaded to the Raspberry Pico Pi (or other Microcontroller running MicroPython). If the large font extension is required the `framebuf2.py` module code should also be uploaded. (See [framebuf2](https://github.com/peter-l5/framebuf2).) 

### Classes

The module includes the classes `SH1107`, `SH1107_I2C` and `SH1107_SPI`.

(description of the `SH1107_I2C` and `SH1107_SPI` classes.)

### Methods and Properties

The following methods and properties are available for controlling the display.<br>
**`poweron()`**<br>
**`poweroff()`** - the display memory is retained in this state, power consumption is reduced to a few uA (tbc).<br>
**`sleep(value)`** - `sleep(0)` calls `poweron()`, `sleep(1)` calls `poweroff()`<br>
**`is_awake()`** this property returns the sleep (False) / wake (True) status of the display.<br>  
**`show(full_update=False)`** - this method updates the display from the framebuffer. It has some optimisation to to update only areas of the screen with changes. To force a complete update of the screen, set the optional `full_update` parameter to `True`. <br>
**`contrast()`** - this command effectively sets the screen brightness. power consumption increases as the screen contrast is increased. valid values are in the range 0 to 255. the SH1107 default power on value is 128, however this module initialises the display with the contrast set to zero.<br>
**`invert(invert)`** - this method inverts the display to black on white, instead of black on white. the parameter `invert` takes the values `True` or `False`.<br>
**`flip(flag=None, update=True)`** - rotates the display by 180 degrees. if no value is provided for `flag` the screen is rotated by 180 degrees from its current orientation, otherwise if the `flag` parameter is set to `True`, the screen rotation is set to 180 degrees.<br>
**`display_start_line()`** - provides some limited scrolling<br>

### Example (I2C)
```
    from machine import Pin, I2C
    import sh1107

    i2c0 = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
    display = sh1107.SH1107_I2C(128, 128, i2c0, address=0x3d, rotate=90)
    display.sleep(False)
    display.fill(0)
    display.text('SH1107', 0, 0, 1)
    display.text('driver', 0, 8, 1)
    display.show()
```
See example code for further details and demo of other methods.

### Example (SPI)

Example usage code for SPI is also provided in the repository.

## Supported displays 

This driver has been tested with a Raspberry Pi Pico and two 128x128 pixel displays, as follows:
- [Adafruit 1.12 inch OLED](https://www.adafruit.com/product/5297 "Adafruit 1.12 inch OLED") (I2C interface, no reset Pin needed in I2C mode) (at 3.3 volts)
- [Pimoroni 1.12 inch OLED](https://shop.pimoroni.com/products/1-12-oled-breakout?variant=12628508704851 "Pimoroni 1.12 inch OLED") (SPI version) (with blocks of pixels lit, this display provides more even brightness with a 5V supply)

Changes to some constants will be needed for 128x64 displays. See annotations in the code.

## Requirements

This code has been tested with MicroPython versions 1.18 and 1.19.1.

## Release notes

#### Release v1.1.0 (build 305)

Changes include:
- `is_awake` property added
- fixed an issue where the negative co-ordinates for framebuffer methods could trip an error 
- fixed an issue where the SPI interface would re-initialise in `SH1107_SPI.write_command()` and `SH1107_SPI.write_data()`
- amended the `fill_rect()` method for compatibility with the "latest" MicroPython release

#### Release v1.0.0 (build 216)

Changes include:
- code tidied up
- annotations added for register values that would need changing for 128x64 displays

#### build 210

Changes include:
- added `set_start_line()` method which implements scrolling in one direction (whether x or y depends on display orientation)
- added `_SET_DISPLAY_OFFSET` constant and included display offset command in start-up sequence. The offset value may need editing for displays smaller than 128x128
- added 100ms sleep after power on command. This is recommended in the SH1107 datasheet and should reduce the risk of EIO interface errors
- added page address = 0 command to start up sequence. This improves reliability of start-up
