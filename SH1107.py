#
# MicroPython SH1107 OLED driver, I2C and SPI interfaces
#
# forked from: https://github.com/robert-hh/SH1106
#
# The MIT License (MIT)
#
# Copyright (c) 2016 Radomir Dopieralski (@deshipu),
#               2017-2021 Robert Hammelrath (@robert-hh)
#               2021 Tim Weber (@scy)
#               2022 peter-l5
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
# Sample code sections for ESP8266 pin assignments
# ------------ SPI ------------------
# Pin Map SPI
#   - 3v - xxxxxx   - Vcc
#   - G  - xxxxxx   - Gnd
#   - D7 - GPIO 13  - Din / MOSI fixed
#   - D5 - GPIO 14  - Clk / Sck fixed
#   - D8 - GPIO 4   - CS (optional, if the only connected device)
#   - D2 - GPIO 5   - D/C
#   - D1 - GPIO 2   - Res
#
# for CS, D/C and Res other ports may be chosen.
#
# from machine import Pin, SPI
# import sh1107

# spi = SPI(1, baudrate=1000000)
# display = sh1107.SH1107_SPI(128, 64, spi, Pin(5), Pin(2), Pin(4))
# display.sleep(False)
# display.fill(0)
# display.text('Testing 1', 0, 0, 1)
# display.show()
#
# --------------- I2C ------------------
#
# Pin Map I2C
#   - 3v - xxxxxx   - Vcc
#   - G  - xxxxxx   - Gnd
#   - D2 - GPIO 5   - SCK / SCL
#   - D1 - GPIO 4   - DIN / SDA
#   - D0 - GPIO 16  - Res
#   - G  - xxxxxx     CS
#   - G  - xxxxxx     D/C
#
# Pin's for I2C can be set almost arbitrary
#
from machine import Pin, I2C
# import sh1107
#
# i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)
# display = sh1107.SH1107_I2C(128, 64, i2c, Pin(16), 0x3c)
# display.sleep(False)
# display.fill(0)
# display.text('Testing 1', 0, 0, 1)
# display.show()

from micropython import const
import time #as time
import framebuf
import gc


# a few register definitions with SH1107 data sheet reference numbers
_MEMORY_ADDRESSING_MODE = const(0x20)    # 3 Set Memory addressing mode #
                                # 0x20 horizontal addressing mode #
                                # 0x21 vertical addressing
_SET_CONTRAST           = const(0x81) # 4 Set Contrast Control  #
_SET_SEGMENT_REMAP      = const(0xa0) # 5. Set Segment Re-map: (A0H - A1H)
_SET_NORMAL_INVERSE     = const(0xa6) # 8. Set Normal/Reverse Display: (A6H -A7H)
_SET_DISPLAY            = const(0xae) # 11. Display OFF/ON: (AEH - AFH)
_SET_SCAN_DIRECTION     = const(0xc0) # 13. Set Common Output Scan Direction: (C0H - C8H)
_LOW_COLUMN_ADDRESS     = const(0x00) # 1. Set Column Address 4 lower bits (POR = 00H) 
_HIGH_COLUMN_ADDRESS    = const(0x10) # 2. Set Column Address 4 higher bits (POR = 10H)  
_SET_PAGE_ADDRESS       = const(0xB0) # 12. Set Page Address (using 4 low bits)


class SH1107(framebuf.FrameBuffer):
    white = const(1)
    black = const(0)

    def __init__(self, width, height, external_vcc, rotate=0):
        print('__init display__ start: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.flip_en = rotate == 180 or rotate == 90
        self.rotate90 = rotate == 90 or rotate == 270
        self.pages = self.height // 8
        self.row_width = self.width //8
        self.bufsize = self.pages * self.width
#        print('pre-buffer: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
        self.renderbuf = bytearray(self.bufsize)
#        print('pre MV: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
        self.renderbuf_mv = memoryview(self.renderbuf)
#        print('MV done: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
#         self.pagebuf = bytearray(self.width)
        self.pages_to_update = 0
#        print('initialising SH1107 class',self.height,self.width,self.pages,self.bufsize)

#        print('pre super call: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
        if self.rotate90:
#             self.displaybuf = bytearray(self.bufsize)
            # HMSB is required to keep the bit order in the render buffer
            # compatible with byte-for-byte remapping to the display buffer,
            # which is in VLSB. Else we'd have to copy bit-by-bit!
            super().__init__(self.renderbuf, self.height, self.width,
                             framebuf.MONO_HMSB)
        else:
#             self.displaybuf = self.renderbuf
            super().__init__(self.renderbuf, self.width, self.height,
                             framebuf.MONO_VLSB)
        

        #self.white =   0xffff
        #self.black =   0x0000

        # flip() was called rotate() once, provide backwards compatibility.
        self.rotate = self.flip
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
#        self.write_command(b'\xd3')    # 9. set display offset 
#        self.write_command(b'\x00')    #    0 is default (POR) display offset value
        self.contrast(0)               # set display to low contrast
        self.poweron()
        # rotate90 requires a call to flip() for setting up.
#         self.flip(self.flip_en, update=False)
#        print('pre flip call: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
        self.flip(self.flip_en)
#        print('disp initialisation done: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
        

    def poweroff(self):
        self.write_command(b'\xAE')

    def poweron(self):
        self.write_command(b'\xAF')

    def flip(self, flag=None, update=True):
        if flag is None:
            flag = not self.flip_en
        mirror_v = flag ^ self.rotate90
        mirror_h =  flag #if self.rotate90 else not flag
        self.write_command( (_SET_SEGMENT_REMAP   | (0x01 if mirror_v else 0x00)).to_bytes(1,'little') )
        self.write_command( (_SET_SCAN_DIRECTION  | (0x08 if mirror_h else 0x00)).to_bytes(1,'little') )
        self.write_command( (_MEMORY_ADDRESSING_MODE | (0x01 if self.rotate90 else 0x00) ).to_bytes(1,'little') )
            
        self.flip_en = flag
        if update:
            self.show(True) # full update

    def sleep(self, value):
        self.write_command( (_SET_DISPLAY | (not value)).to_bytes(1,'little') )

    def contrast(self, contrast):
        # contrast can be between 0 (low), 0x80 (POR) and 0xff (high)
        # the segment current increases with higher values
        
        _commandbuffer2=bytearray(2)
        _commandbuffer2[0] = _SET_CONTRAST
        _commandbuffer2[1] = contrast
#        print(_commandbuffer2)
        self.write_command(_commandbuffer2)
#         self.write_command( ((_SET_CONTRAST << 8) | contrast ).to_bytes(2,'big') )

    def invert(self, invert):
        self.write_command( (_SET_NORMAL_INVERSE | (invert & 1)).to_bytes(1,'little')  )
        
    def show(self, full_update = False):
        _start = time.ticks_us() 
        _commandbuffer=bytearray(3)
        _commandbuffer2=bytearray(2)
        _row_width = self.width // 8
        _current_page = 1
        
        (w, p) = (self.width, self.pages)
                
        if full_update:
            pages_to_update = (1 << self.pages) - 1
        else:
            pages_to_update = self.pages_to_update
        # print("Updating pages: {:016b}".format(pages_to_update))
            
        if self.rotate90:
            for page in range(self.pages):
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
                        i = row * _row_width
                        rb_slice=self.renderbuf_mv[i:(i + _row_width)]
                        self.write_data(rb_slice)
#                         self.write_data(self.renderbuf_mv[i:(i + _row_width)] )
                        #self.write_data(databuffer[i:(i + 16)])
                _current_page <<= 1
                
        else:
            for page in range(self.pages):
                if (pages_to_update & _current_page):
                    _commandbuffer[0] = _SET_PAGE_ADDRESS | page
                    _commandbuffer[1] = _LOW_COLUMN_ADDRESS | 0  # was 2
                    _commandbuffer[2] = _HIGH_COLUMN_ADDRESS | 0
                    self.write_command(_commandbuffer)
                    _page_start=w*page
                    self.write_data(self.renderbuf_mv  [(_page_start):(_page_start+w)])
                _current_page <<= 1
            
        self.pages_to_update = 0
        print('screen update used ',(time.ticks_us()- _start)/1000,'ms')
        print('free memory' , gc.mem_free())

    def pixel(self, x, y, color):
        super().pixel(x, y, color)
        page = y // 8
        self.pages_to_update |= 1 << page

    def text(self, text, x, y, color=1):
        super().text(text, x, y, color)
        self.register_updates(y, y+7)

    def line(self, x0, y0, x1, y1, color):
        super().line(x0, y0, x1, y1, color)
        self.register_updates(y0, y1)

    def hline(self, x, y, w, color):
        super().hline(x, y, w, color)
        self.register_updates(y)

    def vline(self, x, y, h, color):
        super().vline(x, y, h, color)
        self.register_updates(y, y+h)

    def fill(self, color):
        super().fill(color)
        self.pages_to_update = (1 << self.pages) - 1

    def blit(self, fbuf, x, y, key=-1, palette=None):
        super().blit(fbuf, x, y, key, palette)
        self.register_updates(y, y+fbuf.height)

    def scroll(self, x, y):
        # my understanding is that scroll() does a full screen change
        super().scroll(x, y)
        self.pages_to_update =  (1 << self.pages) - 1

    def fill_rect(self, x, y, w, h, color):
        super().fill_rect(x, y, w, h, color)
        self.register_updates(y, y+h)

    def rect(self, x, y, w, h, color):
        super().rect(x, y, w, h, color)
        self.register_updates(y, y+h)

    def register_updates(self, y0, y1=None):
        # this function takes the top and optional bottom address of the changes made
        # and updates the pages_to_change list with any changed pages
        # that are not yet on the list
        start_page = y0 // 8
        end_page = y1 // 8 if y1 is not None else start_page
        # rearrange start_page and end_page if coordinates were given from bottom to top
        if start_page > end_page:
            start_page, end_page = end_page, start_page
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
        self.i2c.writeto(self.address, b'\x40'+buf)

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
            self.spi.write(bytearray([cmd]))
            self.cs(1)
        else:
            self.dc(0)
            self.spi.write(bytearray([cmd]))

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

# testing code
print('Initial free: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
i2c0 = I2C(0, scl=Pin(5), sda=Pin(4), freq=1000000)
print('I2C created: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))

display = SH1107_I2C(128, 128, i2c0, Pin(16), address=0x3d, rotate=90)
print('display created: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))

#display.sleep(False)
print('starting test')
display.fill(white)
display.show()
time.sleep(2)
display.fill(black)
time.sleep(2)
full_update_flag = False
display.text('Testing 1', 0, 0, 1)
display.show(full_update_flag)
display.show(full_update_flag)
time.sleep(1)
display.text('Testing 16', 16, 16, 1)
display.show(full_update_flag)
time.sleep(1)
display.fill_rect(0,17,128,0,1)
display.text('Testing 32', 16, 32, 1)
display.show(full_update_flag)
time.sleep(1)
display
display.text('Testing 120', 16, 120, 1)
display.show(full_update_flag)
time.sleep(1)
display.text('0----+----1----+-', 0, 88, 1)
display.text('01234567890123456', 0, 96, 1)
display.show(full_update_flag)
time.sleep(2)

print('free memory' , gc.mem_free())
for i in range (256):
    display.contrast(i)
    contrast_text='contrast '+str(i)
    display.fill_rect(16,64,96,8,black)
    display.text(contrast_text, 16, 64, 1)
    display.show(full_update_flag)
#     time.sleep_ms(50)

print('free memory' , gc.mem_free())

display.flip()
time.sleep(2)
display.invert(1)
time.sleep(2)
display.invert(0)
time.sleep(2)
display.flip()
time.sleep(2)
display.invert(1)
time.sleep(2)
display.invert(0)
display.fill(black)
display.show()
display.poweroff()


# Pin's for I2C can be set almost arbitrary
#
# from machine import Pin, I2C
# import sh1107
#
# i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)
#display = sh1107.SH1107_I2C(128, 64, i2c, Pin(16), 0x3c)
#display.sleep(False)
#display.fill(0)
#display.text('Testing 1', 0, 0, 1)
#display.show()

