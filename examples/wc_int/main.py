
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
import logging
from WC import WC
from machine import Pin
from credentials import CREDENTIALS

time.sleep(5)

assert len([])==0, "Error with len!"

wc = WC(gaz_sensor=Pin(26), ldr=Pin(27))

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/WC",
    watchdog=None,
    sysinfo_period = 600,
    led_wifi='LED',
    web=True,
    name = "DETECTEUR WC",
    logging_level=logging.DEBUG,
    render_web=wc.render_web
    )

wc.set_iot(iot)
iot.run()