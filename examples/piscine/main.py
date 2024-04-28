# main.py -- put your code here!


from machine import Pin
import logging
import uasyncio as asyncio
import time
import onewire, ds18x20, time
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicAction

time.sleep(5)

#Capteur temperature
ds_sensor = ds18x20.DS18X20(onewire.OneWire(Pin(19)))
print('Found DS devices: ', ds_sensor.scan())

async def get_temp(**kwargs):
    ds_sensor.convert_temp()
    await asyncio.sleep_ms(750)
    roms = ds_sensor.scan()
    #gc.collect()
    if roms:
        return ds_sensor.read_temp(roms[0])

# relay
relay = Pin(5)
relay.init(Pin.OUT)
relay.off()


iot = FmPyIotWeb(
    mqtt_host = "***REMOVED***",
    ssid = 'WIFI_THOME2',
    password = "***REMOVED***",
    mqtt_base_topic = "T-HOME/PISCINE",
    watchdog=100,
    sysinfo_period = 600,
    led_wifi='LED',
    web_credentials=("fred", ***REMOVED***),
    name = "Pompe Piscine",
    logging_level=logging.INFO,
    )

iot.add_topic(Topic("T-HOME/EXTERIEUR/temperature", read=get_temp, send_period=30))
iot.add_topic(TopicAction('./pompe', action = lambda payload : relay.on() if payload == 'ON' else relay.off()))

iot.run()