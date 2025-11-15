
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
import logging
from machine import Pin
from credentials import CREDENTIALS
from test import Test

time.sleep(5)

assert len([])==0, "Error with len!"

test= Test(input_pin=15, output_pin=14, name="TEST_GPIO")

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
    render_web=test.render_web,
    )

test.set_iot(iot)

iot.run()