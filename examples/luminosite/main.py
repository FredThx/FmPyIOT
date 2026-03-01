
import time
from luminosite import Luminosite
from fmpyiot.fmpyiot_web import FmPyIotWeb
import logging
from machine import Pin, SoftI2C 
from credentials import CREDENTIALS

print("Booting...")
print("CTRL-C to exit")
time.sleep(5)
print("Starting luminosity sensor...")

assert len([])==0, "Error with len!"

i2c = SoftI2C(sda=Pin(9), scl=Pin(8), freq=100000)
luminiosite = Luminosite(i2c)

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/SALON/SEMIS",
    watchdog=100,
    sysinfo_period = 600,
    led_wifi='LED',
    web=True,
    name = "Luminosité semis",
    logging_level=logging.INFO,
    device=luminiosite
    )

iot.run()