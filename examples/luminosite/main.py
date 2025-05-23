
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import TopicRead
import logging
from devices.tsl2561 import TSL2561
from machine import I2C, Pin
from credentials import CREDENTIALS

time.sleep(5)

assert len([])==0, "Error with len!"

i2c = I2C(1,sda=Pin(26), scl=Pin(27), freq=100000)
try:
    sensor = TSL2561(i2c, address=0x39)
except OSError:
    sensor = None
    print("TSL2561 not found")

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/SALON/SEMIS",
    watchdog=None,
    sysinfo_period = 600,
    led_wifi='LED',
    web=True,
    name = "Luminosité semis",
    logging_level=logging.DEBUG,
    )

def read_sensor():
    global sensor
    if sensor is None:
        try:
            sensor = TSL2561(i2c, address=0x39)
        except OSError:
            print("TSL2561 not found")
    if sensor:
        try:
            return sensor.read()
        except OSError:
            print("Error reading sensor:")
            sensor = None

iot.add_topic(TopicRead("./LUMINOSITE", read=read_sensor, send_period=10))

iot.run()