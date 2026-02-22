
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
import logging
from relais import Relais
from credentials import CREDENTIALS

time.sleep(5)

relais = Relais(pin_relay1=7,pin_relay2=6)

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/COULOIR_HAUT/ECLAIRAGE",
    watchdog=100,
    sysinfo_period = 600,
    led_wifi='LED',
    name = "Eclairage du couloir du haut",
    logging_level=logging.INFO,
    device=relais
    )

iot.run()