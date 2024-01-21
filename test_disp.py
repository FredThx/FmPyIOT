from machine import I2C, Pin
from ssd1306 import SSD1306_I2C

i2c = I2C(0,scl=1,sda=0)

addr = i2c.scan()[0]

disp = SSD1306_I2C(128,64,i2c,addr)