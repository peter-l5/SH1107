#
# MicroPython SH1107 OLED driver, I2C interfaces
# tested with Raspberry Pi Pico and adafruit 1.12 inch QWIC OLED display
# sh1107 driver v210
#
# The MIT License (MIT)
#
# Copyright (c) 2016 Radomir Dopieralski (@deshipu),
#               2017-2021 Robert Hammelrath (@robert-hh)
#               2021 Tim Weber (@scy)
#               2022 Peter Lumb (peter-l5)
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
# display = sh1107.SH1107_I2C(128, 128, i2c0, Pin(16), address=0x3d, rotate=90)
# display.sleep(False)
# display.fill(0)
# display.text('SH1107', 0, 0, 1)
# display.text('driver', 0, 8, 1)
# display.show()


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
# import framebuf
# print('framebuf is ', ('standard' if _fb_variant ==1 else 'extended') )

import gc


# a few register definitions with SH1107 data sheet reference numbers
_MEMORY_ADDRESSING_MODE = const(0x20)    # 3 Set Memory addressing mode #
                                # 0x20 horizontal addressing mode #
                                # 0x21 vertical addressing
_SET_CONTRAST            = const(0x8100) # 4 Set Contrast Control (double byte command) #
_SET_SEGMENT_REMAP       = const(0xa0) # 5. Set Segment Re-map: (A0H - A1H)
_SET_NORMAL_INVERSE      = const(0xa6) # 8. Set Normal/Reverse Display: (A6H -A7H)
_SET_DISPLAY             = const(0xae) # 11. Display OFF/ON: (AEH - AFH)
_SET_SCAN_DIRECTION      = const(0xc0) # 13. Set Common Output Scan Direction: (C0H - C8H)
_LOW_COLUMN_ADDRESS      = const(0x00) # 1. Set Column Address 4 lower bits (POR = 00H) 
_HIGH_COLUMN_ADDRESS     = const(0x10) # 2. Set Column Address 4 higher bits (POR = 10H)  
_SET_PAGE_ADDRESS        = const(0xB0) # 12. Set Page Address (using 4 low bits)
_SET_DISPLAY_OFFSET      = const(0xD300) # 9. Set Display Offset: (Double Bytes Command)
                                         # second byte may need amending for some displays
                                         # eg 128x64, some require 0xDC60
_SET_DISPLAY_START_LINE  = const(0xDC00) # 17. Set Display Start Line (double byte command)
_SET_MULTIPLEX_RATION    = const(0xA87F) # 6. Set Multiplex Ration: (Double Bytes Command) 


# class SH1107(framebuf.FrameBuffer):
class SH1107(framebuf.FrameBuffer):
    white = const(1)
    black = const(0)
#     MONO_HMSB=super().MONO_HMSB
#     print('SH1107 ',dir(framebuf))

    def __init__(self, width, height, external_vcc, rotate=0):
#         print('__init display__ start: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.flip_en = rotate == 180 or rotate == 90
        self.rotate90 = rotate == 90 or rotate == 270
        self.pages = self.height // 8
        self.row_width = self.width //8
        self.bufsize = self.pages * self.width
#         print('pre-buffer: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
        self.renderbuf = bytearray(self.bufsize)
#         print('pre MV: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
#         self.renderbuf_mv = memoryview(self.renderbuf)
#         print('MV done: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
#         self.pagebuf = bytearray(self.width)
        self.pages_to_update = 0
#         print('initialising SH1107 class',self.height,self.width,self.pages,self.bufsize)

#         print('pre super call: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
        if self.rotate90:
#             self.displaybuf = bytearray(self.bufsize)
            # HMSB is required to keep the bit order in the render buffer
            # compatible with byte-for-byte remapping to the display buffer,
            # which is in VLSB. Else we'd have to copy bit-by-bit!
            super().__init__(self.renderbuf, self.height, self.width,
#                              super().MONO_HMSB)
                             framebuf.MONO_HMSB)
#                              super().MONO_HMSB)
#                              self.MONO_HMSB)
        else:
#             self.displaybuf = self.renderbuf
            super().__init__(self.renderbuf, self.width, self.height,
                             framebuf.MONO_VLSB)
#                              super().MONO_VLSB)

        self.init_display()
        
#         for name in self.__dict__:
#             print(name)
#        print('display __init__ done: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))

    def init_display(self):
#        print('initialise display: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
        self.reset()
        self.fill(self.black)
        self.poweroff()                #turn off OLED display
        self.write_command(b'\xad')    # 10. Set DC-DC Setting (set charge pump enable) 
        self.write_command(b'\x8a')    #     Set DC-DC enable (a=0:disable; a=1:enable)
        self.write_command(b'\xa4')    # 7. Entire Display On/Off
                                       #    0xA4 normal display status
                                       #    0xA5 forcibly turn the display on  
        self.write_command(b'\xa8')    # 6. multiplex ratio 
        self.write_command(b'\x7f')    #    duty = 1/64 [3f]  or 128 [7f]
        self.write_command( (_SET_DISPLAY_OFFSET).to_bytes(2,'big') )  # 9. offset may need changing for some displays
        self.contrast(0)               # set display to low contrast
        self.poweron()
        
        self.write_command((_SET_PAGE_ADDRESS).to_bytes(1,'big')) # set page address to zero
        # rotate90 requires a call to flip() for setting up.
#         self.flip(self.flip_en, update=False)
#        print('pre flip call: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
        self.flip(self.flip_en)
#        print('disp initialisation done: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
        

    def poweroff(self):
        self.write_command(b'\xAE')

    def poweron(self):
        self.write_command(b'\xAF')
        time.sleep_ms(100) # recommended delay in power up sequence

    def flip(self, flag=None, update=True):
        if flag is None:
            flag = not self.flip_en
        mirror_v = flag ^ self.rotate90
        mirror_h =  flag #if self.rotate90 else not flag
        self.write_command( (_SET_SEGMENT_REMAP   | (0x01 if mirror_v else 0x00)).to_bytes(1,'big') )
        self.write_command( (_SET_SCAN_DIRECTION  | (0x08 if mirror_h else 0x00)).to_bytes(1,'big') )
        self.write_command( (_MEMORY_ADDRESSING_MODE | (0x01 if self.rotate90 else 0x00) ).to_bytes(1,'big') )
            
        self.flip_en = flag
        if update:
            self.show(True) # full update

    def sleep(self, value):
        self.write_command( (_SET_DISPLAY | (not value)).to_bytes(1,'big') )

    def set_start_line(self, value):
        # 17. Set Display Start Line:（Double Bytes Command）
        # valid values are 0 (Power on /Reset) to 127 (x00-x7F)
        self.write_command( (_SET_DISPLAY_START_LINE | (value & 0x7F)).to_bytes(2,'big') )
        
    def contrast(self, contrast):
        # 4. contrast can be between 0 (low), 0x80 (POR) and 0xff (high)
        # the segment current increases with higher values
        self.write_command( (_SET_CONTRAST | (contrast & 0xFF)).to_bytes(2,'big') )

    def invert(self, invert):
        self.write_command( (_SET_NORMAL_INVERSE | (invert & 1)).to_bytes(1,'big')  )
        
    def show(self, full_update = False):
        _start = time.ticks_us() 
        _commandbuffer=bytearray(3)
        _commandbuffer2=bytearray(2)
        _current_page = 1
        (w, p) = (self.width, self.pages)
        _row_width = w // 8
        rb_mv = memoryview(self.renderbuf)
                
        if full_update:
            pages_to_update = (1 << p) - 1
        else:
            pages_to_update = self.pages_to_update
#        print("Updating pages : {:016b}".format(pages_to_update), " to top (decimal: ", pages_to_update, ")")
            
        if self.rotate90:
#             rb=self.renderbuf
            for page in range(p):
                # tell display which row
                # print("page",page)
                if (pages_to_update & _current_page):
                    # update 8 display rows
                    for row in range(page*8,(page+1)*8):
                        # set row address for update 
                        # sending 2 commands to the display controller in one i2c write
                        # rather than 2 separate writes speeds up the refresh   
                        _commandbuffer2[0] = row & 0x0f  # low column write address 
                        _commandbuffer2[1] = 0x10 + (row >> 4) # high column write address
                        self.write_command(_commandbuffer2)
                        
                        # take 1 row of data from the screen framebuffer and write to the display
                        _slice_start = row * _row_width
#                         rb_slice=rb_mv[_slice_start:(_slice_start + _row_width)]
#                         self.write_data(rb_slice)
#                         print(rb_slice.__class__)
                        self.write_data(rb_mv[_slice_start:(_slice_start + _row_width)] )
#                         self.write_data(self.renderbuf_mv[i:(i + _row_width)] )
                        #self.write_data(databuffer[i:(i + 16)])
                _current_page <<= 1
                
        else:
            for page in range(p):
                if (pages_to_update & _current_page):
                    _commandbuffer[0] = _SET_PAGE_ADDRESS | page
                    _commandbuffer[1] = _LOW_COLUMN_ADDRESS | 0  # was 2
                    _commandbuffer[2] = _HIGH_COLUMN_ADDRESS | 0
                    self.write_command(_commandbuffer)
                    _page_start=w*page
                    self.write_data(rb_mv [(_page_start):(_page_start+w)])
                _current_page <<= 1
            
        self.pages_to_update = 0
        
#         print('screen update used ', (time.ticks_us()- _start)/1000,'ms')
#         print('free memory' , gc.mem_free())

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

    if _fb_variant == 2:
        def large_text(self, s, x, y, m, c=1):
    #         print('before text call', y, y+(8*m)-1)
            super().large_text(s, x, y, m, c)
    #         print('after text call', y, y+(8*m)-1)
            self.register_updates(y, y+(8*m)-1)

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

    def fill_rect(self, x, y, w, h, c):
        super().fill_rect(x, y, w, h, c)
        self.register_updates(y, y+h-1)

    def rect(self, x, y, w, h, c):
        super().rect(x, y, w, h, c)
        self.register_updates(y, y+h-1)

    def register_updates(self, y0, y1=None):
        y1=min((y1 if y1 is not None else y0), self.height-1)
        # this function takes the top and optional bottom address of the changes made
        # and updates the pages_to_change list with any changed pages
        # that are not yet on the list
        start_page = y0 // 8
        end_page = y1 // 8 if (y1 is not None) else start_page
#         print(y0, y1, start_page, end_page, self.pages_to_update)
        # rearrange start_page and end_page if coordinates were given from bottom to top
        if start_page > end_page:
            start_page, end_page = end_page, start_page
        for page in range(start_page, end_page+1):
            self.pages_to_update |= 1 << page
#         print(y0, y1, start_page, end_page, self.pages_to_update)

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
#         self.temp = bytearray(2)
        if res is not None:
            res.init(res.OUT, value=1)
        super().__init__(width, height, external_vcc, rotate)

#    def write_command(self, cmd):
#        self.temp[0] = 0x80  # Co=1, D/C#=0
#        self.temp[1] = cmd
#        self.i2c.writeto(self.addr, self.temp)

#    def write_data(self, buf):
#        self.i2c.writeto(self.addr, b'\x40'+buf)
                        
    def write_command(self, command_list):
        self.i2c.writeto(self.address, b'\x00'+command_list)
        
    def write_data(self, buf):
#         print('buffer class: ', buf.__class__)
#         _before_write=gc.mem_free()
        self.i2c.writeto(self.address, b'\x40'+buf)
#         _mem_used=gc.mem_free() - _before_write
#         print('lost in i2c write :', _mem_used)

    def reset(self):
        super().reset(self.res)

class SH1107_SPI(SH1107):
    def __init__(self, width, height, spi, dc, res=None, cs=None,
                 rotate=0, external_vcc=False):
        self.rate = 10 * 1000 * 1000
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
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
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
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
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





