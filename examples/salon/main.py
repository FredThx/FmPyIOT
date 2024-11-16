from machine import Pin, I2C
import time, logging
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicIrq
from devices.bmp280 import BMP280
from devices.ds18b20 import DS18b20

from credentials import CREDENTIALS

class Salon:
    
    def __init__(self):
        self.i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400_000)
        self.bmp = BMP280(self.i2c)
        self.ds = DS18b20(27)
        self.detecteur = Pin(26)
        self.params = {}

    def get_pressure(self, **kwargs):
        return self.bmp.pressure/100
    def get_temperature(self, **kwargs):
        return self.ds.read_async()

    def load_params(self, param:dict):
        logging.info("SALON : LOAD PARAMS")
        self.params.update(param)

salon = Salon()

time.sleep(5)

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/SALON",
    watchdog=100,
    sysinfo_period = 600,
    led_incoming="LED", #internal
    led_wifi=16,
    web=True,
    name = "Salon",
    logging_level=logging.INFO,
    )

iot.set_param('salon', default=salon.params, on_change=salon.load_params)

detection_topic = TopicIrq("./detect", pin=salon.detecteur, trigger = Pin.IRQ_RISING + Pin.IRQ_FALLING)
topic_pression = Topic("./PRESSION", read=salon.get_pressure, send_period=30)
topic_temperature = Topic("./temperature", read=salon.get_temperature, send_period=30)

iot.add_topic(topic_pression)
iot.add_topic(topic_temperature)
iot.add_topic(detection_topic)

iot.run()

