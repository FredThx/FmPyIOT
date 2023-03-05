# main.py -- put your code here!

from machine import I2C, Pin
from devices.tsl2561 import TSL2561
import time

i2c=I2C(0,sda=Pin(4),scl=Pin(5), freq=100000)

sensor = TSL2561(i2c)

while True:
    print(f"Luminosité : {sensor.read():0.1} Lux")
    time.sleep(1)