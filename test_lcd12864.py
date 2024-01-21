from machine import Pin, SPI
from lcd12864 import SPI_LCD12864
import random

del len

cs = Pin(5, Pin.OUT, value = 0)
spi = SPI(0, polarity=0, phase = 1,bits=8, sck=Pin(6), mosi=Pin(7))


lcd = SPI_LCD12864(spi=spi, cs=cs)

lcd.text("Hello Fred !", 10,25,1)
lcd.rect(0,0,128,64,1)
lcd.rect(3,3,128-6,64-6,1)

HEART_ICON = [
  [0,0,0,0,0,0,0,0,0,0,0],
  [0,0,1,1,1,0,1,1,1,0,0],
  [0,1,1,0,1,1,1,1,1,1,0],
  [0,1,0,1,1,1,1,1,1,1,0],
  [0,1,1,1,1,1,1,1,1,1,0],
  [0,0,1,1,1,1,1,1,1,0,0],
  [0,0,0,1,1,1,1,1,0,0,0],
  [0,0,0,0,1,1,1,0,0,0,0],
  [0,0,0,0,0,1,0,0,0,0,0],
  [0,0,0,0,0,0,0,0,0,0,0] ]

def draw_icon( lcd, from_x, from_y, icon ):
    for y, row in enumerate( icon ):
        for x, color in enumerate( row ):
            if color==None:
                continue
            lcd.pixel( from_x+x,
                       from_y+y,
                       color )

for x in range(0, 128, len(HEART_ICON[0])):
    for y in range (0, 64, len(HEART_ICON)):
        if random.getrandbits(3)==0:
            draw_icon(lcd, x,y, HEART_ICON)

lcd.update()