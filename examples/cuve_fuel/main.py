
import time
import uasyncio as asyncio
from machine import I2C, Pin
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicAction, TopicRoutine, TopicIrq, TopicOnChange, TopicRead
import logging
from devices.lidar import TF_Luna

time.sleep(5)
i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq = 400_000)
lidar = TF_Luna(i2c, min=20, max=800, freq = 100)
leds = {
    'rouge' : Pin(1, Pin.OUT),
    'vert' : Pin(0,Pin.OUT)
    }


iot = FmPyIotWeb(
    mqtt_host = "***REMOVED***",
    ssid = 'WIFI_THOME2',
    password = "***REMOVED***",
    mqtt_base_topic = "T-HOME/CUVE-FUEL2",
    watchdog=100,
    sysinfo_period = 600,
    led_wifi='LED',
    web_credentials=("fred", ***REMOVED***),
    name = "Cuve de Fuel",
    logging_level=logging.INFO,
    )


iot.add_topic(TopicRead("./distance", read=lambda topic, payload : lidar.distance(), send_period=10))

def set_leds(payload:str):
    logging.info(f"Set led = '{payload}'")
    for key, led in leds.items():
        if key == payload:
            led.on()
        else:
            led.off()

iot.add_topic(TopicAction("./LED", action = lambda topic, payload : set_leds(payload)))


iot.run()