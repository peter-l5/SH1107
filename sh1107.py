#
# MicroPython SH1107 OLED driver, I2C interfaces
# tested with Raspberry Pi Pico and adafruit 1.12 inch QWIC OLED display
# sh1107 driver v310
#
# The MIT License (MIT)
#
# Copyright (c) 2016 Radomir Dopieralski (@deshipu),
#               2017-2021 Robert Hammelrath (@robert-hh)
#               2021 Tim Weber (@scy)
#               2022-2023 Peter Lumb (peter-l5)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#
# Sample code sections for RaspberryPi Pico pin assignments
# ------------ SPI ------------------
# Pin Map SPI
#   - 3v3 - xxxxxx   - Vcc
#   - G   - xxxxxx   - Gnd
#   - D7  - GPIO 15  - TX / MOSI fixed
#   - D5  - GPIO 14  - SCK / Sck fixed
#   - D8  - GPIO 13  - CS (optional, if the only connected device)
#   - D2  - GPIO 21  - DC [Data/Command]
#   - D1  - GPIO 20  - Res [reset]
#
# spi1 = SPI(1, baudrate=10_000_000, sck=Pin(14), mosi=Pin(15), miso=Pin(12))
# display = sh1107.SH1107_SPI(128, 128, spi1, Pin(21), Pin(20), Pin(13))
# display.sleep(False)
# display.fill(0)
# display.text('SH1107', 0, 0, 1)
# display.text('driver', 0, 8, 1)
# display.show()
#
# --------------- I2C ------------------
#
# reset PIN is not needed in some implementations
# Pin Map I2C
#   - 3v3 - xxxxxx   - Vcc
#   - G   - xxxxxx   - Gnd
#   - D2  - GPIO 5   - SCK / SCL
#   - D1  - GPIO 4   - DIN / SDA
#   - D0  - GPIO 16  - Res
#   - G   - xxxxxx     CS
#   - G  - xxxxxx     D/C
#
# using hardware I2C

# from machine import Pin, I2C
# import sh1107
# 
# i2c0 = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
# display = sh1107.SH1107_I2C(128, 128, i2c0, address=0x3d, rotate=90)
# display.sleep(False)
# display.fill(0)
# display.text('SH1107', 0, 0, 1)
# display.text('driver', 0, 8, 1)
# display.show()

__version__ = "v310"
__repo__ = "https://github.com/peter-l5/SH1107"

## SH1107 module code
from micropython import const
import time #as time
# line below is in preparation for possible framebuffer extensions
try:
    import framebuf2 as framebuf
    _fb_variant = 2
except:
    import framebuf
    _fb_variant = 1
print('framebuf is ', ('standard' if _fb_variant ==1 else 'extended') )

#define timed_function decorator
def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = time.ticks_us()
        result = f(*args, **kwargs)
        delta = time.ticks_diff(time.ticks_us(), t)
        print('Function {} Time = {:7.3f}ms'.format(myname, delta/1000))
        return result
    return new_func

# a few register definitions with SH1107 data sheet reference numbers
_LOW_COLUMN_ADDRESS      = const(0x00)   # 1. Set Column Address 4 lower bits (POR = 00H) 
_HIGH_COLUMN_ADDRESS     = const(0x10)   # 2. Set Column Address 4 higher bits (POR = 10H)  
_MEM_ADDRESSING_MODE     = const(0x20)   # 3. Set Memory addressing mode
                                         #    0x20 horizontal addressing; 0x21 vertical addressing
_SET_CONTRAST            = const(0x8100) # 4. Set Contrast Control (double byte command)
_SET_SEGMENT_REMAP       = const(0xa0)   # 5. Set Segment Re-map: (A0H - A1H)
_SET_MULTIPLEX_RATIO     = const(0xA87F) # 6. Set Multiplex Ratio: (Double Bytes Command)
                                         #    duty = 1/64 [3f]  or 128 [7f] (POR)
_SET_NORMAL_INVERSE      = const(0xa6)   # 8. Set Normal/Reverse Display: (A6H -A7H)
_SET_DISPLAY_OFFSET      = const(0xD300) # 9. Set Display Offset: (Double Bytes Command)
                                         #    second byte may need amending for some displays
                                         #    some 128x64 displays (eg Adafruit feather wing 4650)
                                         #    require 0xD360
_SET_DC_DC_CONVERTER_SF  = const(0xad8d) # 10. Set DC-DC Setting (set charge pump enable)
                                         #     Set DC-DC enable (a=0:disable; a=1:enable)
                                         #     0xad81 is POR value and may be needed for 128x64 displays 
_SET_DISPLAY_OFF         = const(0xae)   # 11. Display OFF/ON: (AEH - AFH)
_SET_DISPLAY_ON          = const(0xaf)   # 11. Display OFF/ON: (AEH - AFH)
_SET_PAGE_ADDRESS        = const(0xB0)   # 12. Set Page Address (using 4 low bits)
_SET_SCAN_DIRECTION      = const(0xc0)   # 13. Set Common Output Scan Direction: (C0H - C8H)
_SET_DISPLAY_START_LINE  = const(0xDC00) # 17. Set Display Start Line (double byte command)


class SH1107(framebuf.FrameBuffer):

    def __init__(self, width, height, external_vcc, rotate=0):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.flip_flag = rotate == 180 or rotate == 90
        self.rotate90 = rotate == 90 or rotate == 270
        self.inverse = False
        self.pages = self.height // 8
        self.row_width = self.width // 8
        self.bufsize = self.pages * self.width
        self.renderbuf = bytearray(self.bufsize)
        self.renderbuf_mv = memoryview(self.renderbuf)
        self.pages_to_update = 0
        self._is_awake = False
        if self.rotate90:
            # HMSB is required to keep the bit order in the render buffer
            # compatible with byte-for-byte remapping to the display's memory,
            # which is in VLSB. 
            super().__init__(self.renderbuf, self.height, self.width,
                             framebuf.MONO_HMSB)
        else:
            super().__init__(self.renderbuf, self.width, self.height,
                             framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        self.reset()
        self.poweroff()  #turn off OLED display
        self.fill(0)
        self.write_command( _SET_DC_DC_CONVERTER_SF.to_bytes(2,'big') )
        self.write_command( _SET_MULTIPLEX_RATIO.to_bytes(2,'big') ) 
        self.write_command( _SET_DISPLAY_OFFSET.to_bytes(2,'big') )
        self.write_command( (_MEM_ADDRESSING_MODE | (0x01 if self.rotate90 else 0x00) ).to_bytes(1,'big') )
        self.write_command( _SET_PAGE_ADDRESS.to_bytes(1,'big') ) # set page address to zero
        self.contrast(0) # set display to low contrast
        self.invert(0)   # normal (not inverse) display
        # requires a call to flip() for setting up.
        self.flip(self.flip_flag)
        self.poweron()

    def poweron(self):
        self.write_command(_SET_DISPLAY_ON.to_bytes(1,'big'))
        self._is_awake = True
        time.sleep_ms(100) # SH1107 recommended delay in power on sequence
        
    def poweroff(self):
        self.write_command(_SET_DISPLAY_OFF.to_bytes(1,'big'))
        self._is_awake = False

    def sleep(self, value=True):
        if value == True:
            self.poweroff()
        else:
            self.poweron()
    
    @property
    def is_awake() -> bool:
        return self._is_awake

    def flip(self, flag=None, update=True):
        if flag is None:
            flag = not self.flip_flag
        mirror_v = flag ^ self.rotate90
        mirror_h =  flag 
        self.write_command( (_SET_SEGMENT_REMAP   | (0x01 if mirror_v else 0x00) ).to_bytes(1,'big') )
        self.write_command( (_SET_SCAN_DIRECTION  | (0x08 if mirror_h else 0x00) ).to_bytes(1,'big') )
        self.flip_flag = flag
        if update:
            self.show(True) # full update

    def display_start_line(self, value):
        # 17. Set Display Start Line:（Double Bytes Command）
        # valid values are 0 (Power on /Reset) to 127 (x00-x7F)
        self.write_command( (_SET_DISPLAY_START_LINE | (value & 0x7F)).to_bytes(2,'big') )
        
    def contrast(self, contrast):
        # 4. contrast can be between 0 (low), 0x80 (POR) and 0xff (high)
        # the segment current increases with higher values
        self.write_command( (_SET_CONTRAST | (contrast & 0xFF)).to_bytes(2,'big') )

    def invert(self, invert=None):
        if invert == None:
            invert = not self.inverse
        self.write_command( (_SET_NORMAL_INVERSE | (invert & 1)).to_bytes(1,'big')  )
        self.inverse = invert
    
#     @timed_function
    def show(self, full_update: bool = False):
#         _start = time.ticks_us() 
        (w, p, rb_mv) = (self.width, self.pages, self.renderbuf_mv)
        commandbuffer = bytearray(3)
        commandbuffer2 = bytearray(2)
        current_page = 1
        if full_update:
            pages_to_update = (1 << p) - 1
        else:
            pages_to_update = self.pages_to_update
        if self.rotate90:
            row_bytes = w // 8
            for start_row in range(0, p*8, 8):
                # tell display which row
                if (pages_to_update & current_page):
                    # update 8 display rows
                    for row in range(start_row, start_row + 8):
                        # set row address for update 
                        # sending 2 commands to the display controller in one i2c write
                        # rather than 2 separate writes speeds up the refresh   
                        commandbuffer2[0] = row & 0x0f  # low column write address (low col. cmd is 0x00)
                        commandbuffer2[1] = _HIGH_COLUMN_ADDRESS | (row >> 4) # high column write address
                        self.write_command(commandbuffer2)
                        # take a row of data from the screen framebuffer and write to the display
                        slice_start = row * row_bytes
                        self.write_data(rb_mv[slice_start:(slice_start + row_bytes)])
                current_page <<= 1
        else:
            for page in range(p):
                if (pages_to_update & current_page):
                    commandbuffer[0] = _SET_PAGE_ADDRESS | page
                    commandbuffer[1] = _LOW_COLUMN_ADDRESS
                    commandbuffer[2] = _HIGH_COLUMN_ADDRESS
                    self.write_command(commandbuffer)
                    page_start = w * page
                    self.write_data(rb_mv [(page_start):(page_start+w)])
                current_page <<= 1
        self.pages_to_update = 0
#         print('screen update used ', (time.ticks_us()- _start)/1000,'ms')

    def pixel(self, x, y, c=None):
        if c is None:
            return super().pixel(x, y)
        else:
            super().pixel(x, y , c)
            page = y // 8
            self.pages_to_update |= 1 << page

    def text(self, text, x, y, c=1):
        super().text(text, x, y, c)
        self.register_updates(y, y+7)

    def line(self, x0, y0, x1, y1, c):
        super().line(x0, y0, x1, y1, c)
        self.register_updates(y0, y1)

    def hline(self, x, y, w, c):
        super().hline(x, y, w, c)
        self.register_updates(y)

    def vline(self, x, y, h, c):
        super().vline(x, y, h, c)
        self.register_updates(y, y+h-1)

    def fill(self, c):
        super().fill(c)
        self.pages_to_update = (1 << self.pages) - 1

    def blit(self, fbuf, x, y, key=-1, palette=None):
        super().blit(fbuf, x, y, key, palette)
        self.register_updates(y, y+self.height)

    def scroll(self, x, y):
        # my understanding is that scroll() does a full screen change
        super().scroll(x, y)
        self.pages_to_update =  (1 << self.pages) - 1

    # rect() and fill_rect() amended to be compatible with new rect() method
    # from latest micropython as well as 1.19.1 and previous versions
    def fill_rect(self, x, y, w, h, c):
        try:
            super().fill_rect(x, y, w, h, c)
        except:
            super().rect(x, y, w, h, c, f=True)
        self.register_updates(y, y+h-1)

    def rect(self, x, y, w, h, c, f=None):
        if f == None:
            super().rect(x, y, w, h, c)
        elif f == False:
            super().rect(x, y, w, h, c)
        else:
            try:
                super().rect(x, y, w, h, c, f)
            except:
                super().fill_rect(x, y, w, h, c)   
        self.register_updates(y, y+h-1)

    # conditionally define optimisations for framebuf extension if loaded 
    if _fb_variant == 2:
        def large_text(self, s, x, y, m, c=1):
            super().large_text(s, x, y, m, c)
            self.register_updates(y, y+(8*m)-1)

        def circle(self, x, y, radius, c, f:bool = None):
            super().circle(x, y, radius, c, f)
            self.register_updates(y-radius, y+radius)
        
        def triangle(self, x0, y0, x1, y1, x2, y2, c, f:bool = None):
            super().triangle(x0, y0, x1, y1, x2, y2, c, f)
            self.register_updates(min(y0, y1, y2), max(y0, y1, y2))

    def register_updates(self, y0, y1=None):
        y1=min((y1 if y1 is not None else y0), self.height-1)
        # this function takes the top and optional bottom address of the changes made
        # and updates the pages_to_change list with any changed pages
        # that are not yet on the list
        start_page = y0 // 8
        end_page = (y1 // 8) if (y1 is not None) else start_page
        # rearrange start_page and end_page if coordinates were given from bottom to top
        if start_page > end_page:
            start_page, end_page = end_page, start_page
        # ensure that start and end page values for update are non-negative (-ve is off-screen)
        if end_page >= 0:
            if start_page < 0:
                start_page = 0
            for page in range(start_page, end_page+1):
                self.pages_to_update |= 1 << page

    def reset(self, res):
        if res is not None:
            res(1)
            time.sleep_ms(1)   # sleep for  1 millisecond
            res(0)
            time.sleep_ms(20)  # sleep for 20 milliseconds
            res(1)
            time.sleep_ms(20)  # sleep for 20 milliseconds


class SH1107_I2C(SH1107):
    def __init__(self, width, height, i2c, res=None, address=0x3d,
                 rotate=0, external_vcc=False):
        self.i2c = i2c
        self.address = address
        self.res = res
        if res is not None:
            res.init(res.OUT, value=1)
        super().__init__(width, height, external_vcc, rotate)
                        
#     @timed_function
    def write_command(self, command_list):
        self.i2c.writeto(self.address, b'\x00'+command_list)
        
#     @timed_function
    def write_data(self, buf):
        self.i2c.writeto(self.address, b'\x40'+buf)

    def reset(self):
        super().reset(self.res)

class SH1107_SPI(SH1107):
    def __init__(self, width, height, spi, dc, res=None, cs=None,
                 rotate=0, external_vcc=False):
        dc.init(dc.OUT, value=0)
        if res is not None:
            res.init(res.OUT, value=0)
        if cs is not None:
            cs.init(cs.OUT, value=1)
        self.spi = spi
        self.dc = dc
        self.res = res
        self.cs = cs
        super().__init__(width, height, external_vcc, rotate)

    def write_command(self, cmd):
        if self.cs is not None:
            self.cs(1)
            self.dc(0)
            self.cs(0)
            self.spi.write(cmd)
            self.cs(1)
        else:
            self.dc(0)
            self.spi.write(cmd)

    def write_data(self, buf):
        if self.cs is not None:
            self.cs(1)
            self.dc(1)
            self.cs(0)
            self.spi.write(buf)
            self.cs(1)
        else:
            self.dc(1)
            self.spi.write(buf)

    def reset(self):
        super().reset(self.res)