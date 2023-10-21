# MicroPython SH1107 display driver for 128x128 and 128x64 pixel displays - with large text, triangles and circles

MicroPython driver for SH1107-based OLED displays with support for I2C and SPI connections. This driver works with 128x128 and 128x64 pixel displays. (For a list of tested displays, see: [tested displays](#tested-displays), below.)

This driver was derived from the [SH1106 driver](https://github.com/robert-hh/SH1106) made by @robert-hh and others. It has been adapted for the SH1107 and incorporates several enhancements.

The large text, triangle and circle methods in the MicroPython FrameBuffer extension [framebuf2](https://github.com/peter-l5/framebuf2) are supported, as are the ellipse and poly methods added to the FrameBuffer class in MicroPython version 1.20.0.

Note: from version release v1.3.0 (build v317) which added support for 128x64 displays, the use of the rotate parameter has changed. Thus, for a previous setting of 90 (degrees), 0 should now be used and similarly for 0, 180, and 270, values of 270, 90 and 180 respectively should be used instead.

## Features and performance

This driver offers **screen rotation**: the screen can be initialised at 0, 90, 180 or 270 degrees rotation. The rotation can be changed by 180 degrees after initialisation, but not by 90 degrees clock-wise or anti-clockwise. This is because 90 and 270 degrees use a different framebuffer mode and screen updating method which are set on initialisation.

The driver includes some optimisation for partial screen updates which typically reduce the amount of data written to the screen and increase the speed of updates and display responsiveness. With an I2C connection at 400,000 bps a 128x128 display will achieve about 16 frames per second when orientated at 90 or 270 degrees and 10 frames per second at 0 or 180 degrees. Partial updates are faster, for example, 1 row of text can be updated in around 5 milliseconds (tested values using a Raspberry Pi pico at standard clock speed). Faster updates can be achieved by running the I2C connection at 1,000,000 bps (although this is faster than the rated speed for the SH1107).<br>
An SPI connection at 40 MHz can achieve full screen updates in around 5ms when orientated at 90 or 270 degrees and about 20ms at 0 or 180 degrees. Updates for 128x64 displays are faster.

The driver builds in the facility to use the **`large_text()`**, **`triangle()`** and **`circle()`** methods in the MicroPython FrameBuffer extension [framebuf2](https://github.com/peter-l5/framebuf2). Moreover, some limited **hardware scrolling** functionality can be used with the `display_start_line()` method.

## Display connection

### I2C
SCL and SDA have to be connected as minimum. The driver can reset the device with the reset PIN (this is not required for some displays, for example those tested).

### SPI
SCLK, MOSI, D/C are always required. If the display is the only SPI device, CS may be tied to GND. Reset has also to be connected, unless it is driven by an external circuit.

## Usage

The [sh1107.py module code](/sh1107.py) should be uploaded to the Raspberry Pico Pi (or other Microcontroller running MicroPython). The large font, triangle and circles extension is added by additionally uploading the `framebuf2.py` module code. (See [framebuf2](https://github.com/peter-l5/framebuf2).) 

## Classes

The module includes the class `SH1107` and the derived classes `SH1107_I2C` and `SH1107_SPI`. The I2C and SPI classes provide equivalent methods. 

### I2C
```
display = sh1107.SH1107_I2C(width, 
                            height, 
                            i2c, 
                            res=None, 
                            address=0x3d, 
                            rotate=0, 
                            external_vcc=False,
                            delay_ms=200)
```
- width (always 128) and height (128 or 64) define the size of the display
- i2c is an I2C object, which has to be created beforehand, and sets the SDA and SCL pins
- res is the optional GPIO Pin object for the reset connection
- address is the I2C address of the display. Default value is 0x3d (or 61 in decimal)
- rotate defines display content rotation in degrees (can be 0, 90, 180 or 270)
- delay_ms sets a delay in milliseconds in the display power on sequence and wake from sleep
  (the SH1107 datasheet suggests a 100ms delay, in practice a 200ms seems more effective
   in reducing I2C communication errors)

### SPI
```
display = sh1107.SH1107_SPI(width, 
                            height, 
                            spi, 
                            dc, 
                            res=None, 
                            cs=None, 
                            rotate=0, 
                            external_vcc=False,
                            delay_ms=100)
```
- width (always 128) and height (128 or 64) define the size of the display
- spi is an SPI object, which has to be created beforehand, and sets the SCL and MOSI pins
MISO is not used
- dc is the GPIO Pin object for the Data/Command selection
- res is the optional GPIO Pin object for the reset connection
- cs is the optional GPIO Pin object for the CS connection
- rotate defines display content rotation in degrees (can be 0, 90, 180 or 270)
- delay_ms sets a delay in milliseconds in the display power on sequence and wake from sleep
  (the SH1107 datasheet suggests a 100ms delay)

## Methods and Properties

The following methods and properties are available for controlling the display<br>
**`poweron()`**<br>
**`poweroff()`** - the display memory is retained in this state, power consumption is reduced to a <5uA for the display (other components on a board may increase this, of course)<br>
**`sleep(value)`** - `sleep(0)` calls `poweron()`; `sleep()` or `sleep(1)` calls `poweroff()`<br>
**`is_awake()`** this property returns the sleep (False) / wake (True) status of the display<br>
**`show(full_update=False)`** - this method updates the display from the framebuffer. It has some optimisation to to update only areas of the screen with changes. To force a complete update of the screen, set the optional `full_update` parameter to `True`<br>
**`contrast()`** - this command effectively sets the screen brightness. segment power consumption is proportional to screen contrast. valid values are in the range 0 to 255. the SH1107 default power on value is 128, however this module initialises the display with the contrast set to zero<br>
**`invert(invert)`** - this method inverts the display to black on white, instead of black on white. the parameter `invert` takes the values `True` or `False`<br>
**`flip(flag=None, update=True)`** - if no value is provided for the `flag` parameter the screen is rotated by 180 degrees from its current orientation, otherwise if the `flag` parameter is set to `True`, the screen rotation is set to 180 degrees, or 0 degrees for `False`. A full screen update is performed unless `update` is set to `False`<br>
**`display_start_line()`** - provides some limited scrolling<br>

## FrameBuffer methods

The driver works with all [MicroPython FrameBuffer drawing methods](https://docs.micropython.org/en/v1.20.0/library/framebuf.html "MicroPython FrameBuffer v1.20.0") (as at MicroPython 1.20.0). The syntax of the `fill_rect` method available in versions 1.19.1 and earlier (but not 1.20.0) is also supported.

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
See example code for further details and usage demonstrations of other methods. (The example code was written for 128x128 displays and has only been partially adapted for 64x128 displays.)

### Example (SPI)

Example code for SPI is included in the repository. (The code was written for 128x128 displays
and has only been partially adapted for 64x128 displays.)  

## Tested displays 

This driver has been tested with a Raspberry Pi Pico and the displays listed below. It should work with other 128x128 and 128x64 size displays. (Whilst the code works with the tested displays, other 128x64 displays *might* need changes to some setup/control parameters, depending on how the display panel is connected to the driver IC.)

### 128x128 displays

- [Adafruit 1.12 inch OLED](https://www.adafruit.com/product/5297 "Adafruit 1.12 inch OLED") (128x128 pixels, tested with I2C interface, no reset Pin needed in I2C mode) (at 3.3 volts)
- [Pimoroni 1.12 inch OLED](https://shop.pimoroni.com/products/1-12-oled-breakout?variant=12628508704851 "Pimoroni 1.12 inch OLED") (128x128 pixels, SPI version tested) (with blocks of pixels lit, this display was found to provide more even brightness with a 5V rather than 3.3V supply)

### 128x64 displays

- [Adafruit FeatherWing OLED - 128x64 OLED](https://www.adafruit.com/product/4650 "Adafruit FeatherWing OLED - 128x64 OLED") (I2C interface tested via STEMMA QT/ Qwiic connector)
- [Waveshare 1.3 inch OLED Module (C)](https://www.waveshare.com/wiki/1.3inch_OLED_Module_(C) "Waveshare 1.3inch OLED Module (C)") (128x64 pixels, default SPI interface tested)

## Requirements

This code has been tested with MicroPython versions 1.18, 1.19.1 and 1.20.0.

The MicroPython FrameBuffer extension [framebuf2](https://github.com/peter-l5/framebuf2) is recommended for its large text, triangle and circle methods.

## Release notes

#### release v1.3.2 (build 319)

- fixes an error in the is_awake() property
- parameterizes the power on / wake from sleep delay
- adds additional SH1107 commands to the start-up sequence (all set to defaults)
- amends the DC-DC converter setting to the SH1107 power on reset default of `0xad81` from `0xad8d`   


#### Release v1.3.0 (build 317)

- adds support for 128x64 displays and the ellipse and poly methods in MicroPython 1.20.0
- usage of the rotate parameter is amended (see above) 

#### Release v1.2.0 (build 311)

- optimisation for the rotation feature of the large_text() method of the framebuf2 module added 

#### build 310

- updated optimisations for the circle and triangle method of the framebuf2 module added 
- repaired a logic error in the sleep method 

#### Release v1.1.0 (build 305)

- `is_awake` property added
- fixed an issue where the negative co-ordinates for framebuffer methods could trip an error 
- fixed an issue where the SPI interface would re-initialise in `SH1107_SPI.write_command()` and `SH1107_SPI.write_data()`
- amended the `fill_rect()` method for compatibility with the "latest" MicroPython release

#### Release v1.0.0 (build 216)

- code tidied up
- annotations added for register values that would need changing for 128x64 displays

#### build 210

- added `set_start_line()` method which implements scrolling in one direction (whether x or y depends on display orientation)
- added `_SET_DISPLAY_OFFSET` constant and included display offset command in start-up sequence. 
- added 100ms sleep after power on command in line with diagrams in the SH1107 datasheet
- added page address = 0 command to start up sequence. This improves reliability of start-up
