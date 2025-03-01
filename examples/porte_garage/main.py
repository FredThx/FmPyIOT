from machine import Pin
import logging
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicOnChange
from porte_garage import PorteGarage

from credentials import CREDENTIALS

time.sleep(5)

porte_garage = PorteGarage(
    sensor_close = Pin(21),
    sensor_open = Pin(20),
    gate_motor_push = Pin(19))

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    mqtt_base_topic = "T-HOME/GARAGE/PORTE",
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    watchdog=100,
    sysinfo_period = 600,
    led_wifi='LED',
    name = "Porte de garage",
    logging_level=logging.INFO,
    )

iot.set_param('push_duration', default=1.0, on_change = lambda value : porte_garage.set_push_duration(float(value)))

iot.add_topic(Topic("./etat", read=lambda topic, payload : porte_garage.get_gate_state(), send_period=60))
iot.add_topic(TopicOnChange("./etat", read=lambda topic, payload : porte_garage.get_gate_state(), period=5))
iot.add_topic(Topic('./push', action = lambda payload : porte_garage.push_button_async()))

iot.run()