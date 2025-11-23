#from devices.ds18b20 import DS18b20
#from devices.fdht import DHT22
from machine import Pin, I2C
from fmpyiot.fmpyiot_web import FmPyIotWeb
from reservoir import Reservoir
from devices.lps35hw import LPS35HW
from devices.bmp280 import BMP280
from credentials import CREDENTIALS
import logging

try:
    len([])
except:
    del len

i2c = I2C(1, scl=Pin(27), sda=Pin(26))
lps = LPS35HW(i2c, address=0x5D)  # Capteur de pression au fond du réservoir
try:
    bmp = BMP280(i2c)  # Capteur de pression hors du réservoir
except OSError:
    bmp = None
reservoir = Reservoir(lps, bmp, max_height=100, name="reservoir")

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/SERRE/RESERVOIR",
    watchdog=100,
    sysinfo_period = 600,
    logging_level= logging.INFO,
    name="Reservoir de la Serre de Fred",
    description="Des capteur de pression pour mesurer le niveau d'eau dans le réservoir de la serre",
    device=reservoir
    )

iot.run()
