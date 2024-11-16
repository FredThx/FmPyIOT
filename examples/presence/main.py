from machine import Pin
import time, logging
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import TopicIrq

from credentials import CREDENTIALS

detecteur = Pin(15,Pin.IN)

time.sleep(5)

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/BUREAU/DETECTION",
    watchdog=100,
    sysinfo_period = 600,
    led_incoming="LED", #internal
    led_wifi=16,
    web=True,
    name = "Bureau Detection",
    logging_level=logging.INFO,
    )

detection_topic = TopicIrq("./detect", pin=detecteur, trigger = Pin.IRQ_RISING)

iot.add_topic(detection_topic)


iot.run()
