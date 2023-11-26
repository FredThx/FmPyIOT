
import time
import uasyncio as asyncio
from machine import I2C, Pin
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicAction, TopicRoutine, TopicIrq, TopicOnChange, TopicRead
import logging
from devices.lidar import TF_Luna

time.sleep(5)
i2c = I2C(0, scl=Pin(13), sda=Pin(12), freq = 400_000)
lidar = TF_Luna(i2c, min=20, max=800, freq = 100)

niveau_bas = Pin(14, Pin.OUT)
niveau_haut = Pin(15, Pin.OUT)


iot = FmPyIotWeb(
    #mqtt_host = "***REMOVED***",
    mqtt_host = "192.168.0.11",
    #ssid = 'WIFI_THOME2',
    #password = "***REMOVED***",
    ssid = 'OLFA_PRESSES',
    password = "79073028",
    #ssid = 'OLFA_WIFI',
    #password = "Olfa08SignyLePetit",
    mqtt_base_topic = "OLFA/CUVE-SCIURE",
    watchdog=100,
    sysinfo_period = 600,
    led_wifi='LED',
    web_credentials=("olfa", "tr0ne"),
    name = "Cuve de Sciure",
    logging_level=logging.INFO,
    )


iot.add_topic(TopicRead("./distance", read=lambda topic, payload : lidar.distance(), send_period=10))

async def test_distance():
    while True:
        distance = lidar.distance()
        print(distance)
        if distance < 100: #Niveau haut
            niveau_haut.on()
        else:
            niveau_haut.off()
        if distance > 200: #Niveau bas
            niveau_bas.on()
        else:
            niveau_bas.off()
        await asyncio.sleep(0.1)


iot.add_routine(TopicRoutine(test_distance))

iot.run()