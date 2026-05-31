
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
import logging
from arrivee_eau import ArriveeEau
from credentials import CREDENTIALS

time.sleep(5)

arrivee = ArriveeEau(pin_valve=7, pin_flowmeter=27)

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/ARRIVEE-EAU/",
    watchdog=100,
    sysinfo_period = 600,
    led_wifi='LED',
    name = "Arrivée d'Eau",
    logging_level=logging.INFO,
    device=arrivee
    )

iot.run()