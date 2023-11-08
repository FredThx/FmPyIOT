
import time
import uasyncio as asyncio
from machine import Pin
from fmpyiot.fmpyiot import FmPyIot
from fmpyiot.topics import Topic, TopicAction, TopicRoutine, TopicIrq, TopicOnChange, TopicRead
import logging
from devices.sen0311 import Sen0311

time.sleep(5)

ultra_sonic=Sen0311(1) #UART 1 (Tx = GPIO 4/ Rx = GPIO 5)
niveau_bas = Pin(14, Pin.OUT)
niveau_haut = Pin(15, Pin.OUT)


iot = FmPyIot(
    mqtt_host = "***REMOVED***",
    mqtt_base_topic = "OLFA/CUVE-SCIURE",
    ssid = 'WIFI_THOME2',
    password = "***REMOVED***",
    watchdog=100,
    sysinfo_period = 600,
    led_wifi='LED',
    web=True,
    web_credentials=("olfa", "tr0ne"),
    name = "Cuve de Sciure",
    logging_level=logging.INFO,
    )


iot.add_topic(TopicRead("./distance", lambda topic, payload : ultra_sonic.get_distance_async(), send_period=10))

async def test_distance():
    while True:
        distance = await ultra_sonic.get_distance_async()
        if distance < 1000: #Niveau haut
            niveau_haut.on()
        else:
            niveau_haut.off()
        if distance > 2000: #Niveau bas
            niveau_bas.on()
        else:
            niveau_bas.off()
        await asyncio.sleep(0.1)


iot.add_routine(TopicRoutine(test_distance))


iot.run()