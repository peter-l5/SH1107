# sh1107 driver demo code v204
# this code is intended for a 128*128 pixel display

from machine import Pin, I2C
import sh1107
print('dir sh1107: ', dir(sh1107))
import gc
import sys
import time #as time
import framebuf


# basic test code
i2c0 = I2C(0, scl=Pin(5), sda=Pin(4), freq=1000000)
display = sh1107.SH1107_I2C(128, 128, i2c0, Pin(16), address=0x3d, rotate=90)
display.sleep(False)
display.fill(0)
display.text('SH1107', 0, 0, 1)
display.text('driver', 0, 8, 1)
display.show()


# full test code
print('version ',sys.implementation)
print('Initial free: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
i2c0 = I2C(0, scl=Pin(5), sda=Pin(4), freq=1000000)
print('I2C created: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))

display = sh1107.SH1107_I2C(128, 128, i2c0, Pin(16), address=0x3d, rotate=90)
print('display created: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))

#display.sleep(False)
print('starting test')
display.fill(1)
display.show()
time.sleep(2)
display.fill(0)
time.sleep(2)
full_update_flag = False
display.text('Testing 1', 0, 0, 1)
display.show(full_update_flag)
display.show(full_update_flag)
time.sleep(1)
display.text('Testing 16', 16, 16, 1)
display.show(full_update_flag)
time.sleep(1)
display.fill_rect(0, 26, 128, 4, 1)
# display.text('Testing 32', 16, 32, 1)
display.show(full_update_flag)
time.sleep(1)
display
display.text('Testing 120', 16, 120, 1)
display.show(full_update_flag)
time.sleep(1)
display.text('0----+----1----+-', 0, 88, 1)
display.text('01234567890123456', 0, 96, 1)
for i in range (16):
    p=display.pixel(i,96)
#     p=i // 10
    display.text(str(p),i*8,104)
    for j in range (4):
        display.pixel(i*8+j*2,114,1)
        

display.show(full_update_flag)
print('bilt test')
smallbuffer=bytearray(8)
letter=framebuf.FrameBuffer(smallbuffer,8,8,framebuf.MONO_HMSB)
print('letter dir', dir(letter))
letter.text('K',0,0,1)
display.blit(letter,0,56)
display.show(full_update_flag)

print('large text test')
try:
    display.large_text('QuiteBIG', 0, 32, 2, 1)
except:
    display.text('framebuf2', 0, 40 ,1)
    display.text('not loaded', 0, 48, 1)
    
display.show(full_update_flag)
time.sleep(2)

# print('free memory' , gc.mem_free())
# for i in range (256):
#     display.contrast(i)
#     contrast_text='contrast '+str(i)
#     display.fill_rect(16,64,96,8,0)
#     display.text(contrast_text, 16, 64, 1)
#     display.show(full_update_flag)
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
time.sleep(1)
display.fill(0)
display.show(full_update_flag)


print('large text test 3')
try:
    display.large_text('BIGx3', 0, 0, 3, 1)
except:
    display.text('large_text', 0, 0, 1)
    display.text('method from', 0, 8, 1)
    display.text('framebuf2', 0, 16 ,1)
    display.text('not loaded', 0, 24, 1)
display.show(full_update_flag)

print('large text test 4')
try: 
    display.large_text('HUGE', 0, 64, 4, 1)
except:
    pass
display.show(full_update_flag)

time.sleep(5)
display.fill(0)
display.show()


print('large text test 4')
try:
    display.large_text('1', 0, 0, 16, 1)
    display.show()
    time.sleep(1)
    display.fill(0)
    display.large_text('2', 0, 0, 16, 1)
    display.show()
    time.sleep(1)
    display.fill(0)
    display.large_text('3', 0, 0, 16, 1)
    display.show()
    time.sleep(1)
    display.fill(0)
    display.large_text('!', 0, 0, 16, 1)
    display.show()
    time.sleep(1)
    display.invert(1)
    time.sleep(1)
    display.invert(0)
    time.sleep(1)
    display.invert(1)
    time.sleep(1)
    display.invert(0)
    time.sleep(1)
except:
    pass

display.fill(0)
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
