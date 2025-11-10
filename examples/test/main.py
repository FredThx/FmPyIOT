
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
import logging
from machine import Pin
from credentials import CREDENTIALS

time.sleep(5)

assert len([])==0, "Error with len!"

def render():
    return "<H3>Hello World!</H3>"

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/TEST",
    watchdog=None,
    sysinfo_period = 600,
    led_wifi='LED',
    web=True,
    name = "TEST",
    logging_level=logging.DEBUG,
    render_web=render,
    )

iot.run()