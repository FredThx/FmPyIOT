from machine import Pin, I2C
import uasyncio as asyncio
import time, logging
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicIrq, TopicRoutine
from devices.bmp280 import BMP280
from devices.ds18b20 import DS18b20



i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400_000)

bmp = BMP280(i2c)

ds = DS18b20(27)

time.sleep(5)

iot = FmPyIotWeb(
    mqtt_host = "***REMOVED***",
    mqtt_base_topic = "T-HOME/SALON",
    ssid = 'WIFI_THOME2',
    password = "***REMOVED***",
    watchdog=100,
    sysinfo_period = 600,
    led_incoming="LED", #internal
    led_wifi=16,
    web=True,
    web_credentials=(***REMOVED***, ***REMOVED***),
    name = "Salon",
    logging_level=logging.INFO,
    )

#detection_topic = TopicIrq("./detect", pin=detecteur, trigger = Pin.IRQ_RISING)
#iot.add_topic(detection_topic)
topic_pression = Topic("./PRESSION", read=lambda topic, payload: bmp.pressure/100, send_period=30)
topic_temperature = Topic("./temperature", read=lambda topic, payload : ds.read_async(), send_period=30)

iot.set_param("period_temperature", default=30, on_change= lambda period : topic_temperature.set_send_period(period))
iot.set_param("period_pression", default=30, on_change= lambda period : topic_pression.set_send_period(period))

iot.add_topic(topic_pression)
iot.add_topic(topic_temperature)

iot.run()

