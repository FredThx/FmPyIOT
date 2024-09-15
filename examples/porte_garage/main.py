# main.py -- put your code here!


from machine import Pin
import logging
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic
from porte_garage import PorteGarage

time.sleep(5)

porte_garage = PorteGarage(
    sensor_close = Pin(21),
    sensor_open = Pin(20),
    gate_motor_push = Pin(19))

iot = FmPyIotWeb(
    mqtt_host = "***REMOVED***",
    ssid = 'WIFI_THOME2',
    password = "***REMOVED***",
    mqtt_base_topic = "T-HOME/GARAGE/PORTE",
    watchdog=100,
    sysinfo_period = 600,
    led_wifi='LED',
    web_credentials=("fred", ***REMOVED***),
    name = "Porte de garage",
    logging_level=logging.INFO,
    )

iot.set_param('push_duration', default=1.0, on_change = lambda value : porte_garage.set_push_duration(float(value)))

iot.add_topic(Topic("./etat", read=lambda topic, payload : porte_garage.get_gate_state(), send_period=5))
iot.add_topic(Topic('./push', action = lambda payload : porte_garage.push_button_async()))

iot.run()