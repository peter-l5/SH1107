# sh1107 driver demo code v319
# this code is intended for a 128*128 pixel display

print('starting test')

from machine import Pin, I2C, SoftI2C
import sh1107
print('dir sh1107: ', dir(sh1107))
import gc
import sys
import time #as time
import framebuf
import array


# # basic test code I2C
# i2c0 = SoftI2C(scl=Pin(5), sda=Pin(4), freq=400000)
i2c0 = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
print('I2C scan: ',i2c0.scan())
# display = sh1107.SH1107_I2C(128, 128, i2c0, Pin(16), address=0x3d, rotate=90)
display = sh1107.SH1107_I2C(128, 64, i2c0, address=60, rotate=0)
#time.sleep(0.5)
# display.sleep(False)
display.fill(0)
display.text('SH1107', 0, 0, 1)
display.text('driver', 0, 8, 1)
display.show()
time.sleep(1)
display.fill(0)
display.show()

# full test code
print('version ',sys.implementation)
print('Initial free memory: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
i2c0 = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
print('I2C scan: ',i2c0.scan())
print('I2C created: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
display = sh1107.SH1107_I2C(128, 64, i2c0, address=60, rotate=90)
# display = sh1107.SH1107_I2C(128, 128, i2c0, Pin(16), address=0x3d, rotate=0)
print('display created: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))


## common I2C and SPI test code below ##

display.sleep(False)
display.fill(0)
display.text('SH1107', 0, 0, 1)
display.text('driver', 0, 8, 1)
display.show()
time.sleep(1)

display.fill(0)
display.show()
if sh1107._fb_variant == 2:
    for i in range(17):
        display.large_text(str(i % 10), 0, 0, max(i,1), c=1, r=90*i)
        display.show()
        time.sleep(0.1)
        display.fill(0)
    for i in range(5):
        for j in range(5):
            display.large_text(str("big text"), (i) % 2 *56, (i+1) % 2 *56, 2, 1, 90*i, 90*j)
            display.show()
            time.sleep(.2)
            display.fill(0)
    print('framebuf2 framebuffer extension tests: triangles and circles')
    for i in range (0, 32, 4):
        display.triangle(0+3*i, i, 127-i, i, 127-i, 127-3*i, c=1)
        display.show()
    for i in range (0, 32, 4):
        display.triangle(i, 0+3*i, i, 127-i, 127-3*i, 127-i, c=1)
        display.show()
    time.sleep(2)
    display.fill(0)
#     display.show()
#     display.triangle(0, 0, 0, 127, 127, 127, c=1, f=True) 
#     display.show()
#     time.sleep(2)
    display.fill(0)
    display.show()
    for i in range (0, 64, 4):
        display.circle(64, 64, 64-i , c=1)
        display.show()
    time.sleep(2)
    display.fill(0)
    display.show()
    for i in range (0, 128, 32):
        for j in range (0, 128, 32):
            display.rect(i, j, 32, 32, c=(i+j)//32 % 2, f=True)
            display.show()
            display.circle(i+16, j+16, 15 , c=((i+j)//32 +1) % 2, f=True)
            display.show()
    time.sleep(2)
    display.fill(0)
    display.show()


#display.sleep(False)
display.fill(1)
display.show()
display.show()
time.sleep(1)
display.fill(0)
time.sleep(1)
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
    
display.show(True)
# sys.exit(0)
time.sleep(2)

print('contrast demo')
print('free memory' , gc.mem_free())
for i in range (256):
    display.contrast(i)
    contrast_text='contrast '+str(i)
    display.fill_rect(16,64,96,8,0)
    display.text(contrast_text, 16, 64, 1)
    display.show(full_update_flag)
    time.sleep_ms(25)
    
display.contrast(0x5F)

print('scroll test (start line)')
print('free memory' , gc.mem_free())
for i in range (128):
    display.display_start_line(i)
    time.sleep_ms(4)
for i in range (128):
    display.display_start_line(127-i)
    time.sleep_ms(4)

display.display_start_line(0)
time.sleep_ms(500)

print('free memory' , gc.mem_free())


print('invert test')
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

time.sleep(2)
display.fill(0)
display.show()

print('large text test 16')
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

time.sleep(1)

for i in range(64):
    display.rect(i, i, 128-i*2, 128-i*2, c = i % 2)
    display.show()
#     time.sleep_ms(10)
time.sleep(1)
display.fill(0)
display.show()

for i in range(64):
    display.rect(i, i, 128-i*2, 128-i*2, c = i % 2, f=False)
#    display.sleep(i % 2)  
    display.show()
    
time.sleep(1)
display.fill(0)
display.show()

for i in range(64):
    display.rect(i, i, 128-i*2, 128-i*2, c = i % 2, f=True)
#    display.sleep(i % 2)
    display.show()

# time.sleep(1)
# display.fill(0)
# display.show()
# 
# for i in range(64):
#     display.fill_rect(i, i, 128-i*2, 128-i*2, c = i % 2)
# #    display.sleep(i % 2)
#     display.show()
    
# for i in range(64):
#     display.sleep(i % 2)

time.sleep(2)
display.fill(0)
display.show()
display.show()
display.show()
display.show()
display.show()
display.show()
display.show()
display.show()
display.show()
display.show()

display.ellipse(64, 48, 56, 32, 1)
display.show()
time.sleep(1)
display.ellipse(64, 48, 56, 32, 1, 1, 0xD)
display.show()
time.sleep(1)
coords=array.array('h', [0,0,0,40,40,40 ])
print(coords)
display.fill(0)
display.poly(10,10,coords, 1,1)
display.show()
time.sleep(3)

display.poweroff()

