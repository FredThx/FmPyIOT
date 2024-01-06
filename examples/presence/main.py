from machine import Pin
import time, logging
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicIrq

detecteur = Pin(15,Pin.IN)

time.sleep(5)


iot = FmPyIotWeb(
    mqtt_host = "***REMOVED***",
    mqtt_base_topic = "T-HOME/BUREAU/DETECTION",
    ssid = 'WIFI_THOME2',
    password = "***REMOVED***",
    watchdog=100,
    sysinfo_period = 600,
    led_incoming="LED", #internal
    led_wifi=16,
    web=True,
    web_credentials=(***REMOVED***, ***REMOVED***),
    name = "Bureau Detection",
    logging_level=logging.INFO,
    )


detection_topic = TopicIrq("./detect", pin=detecteur, trigger = Pin.IRQ_RISING)


iot.add_topic(detection_topic)
iot.run()
