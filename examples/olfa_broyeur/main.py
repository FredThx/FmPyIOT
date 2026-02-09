
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
import logging
from humidite import Humidity
from credentials import CREDENTIALS

time.sleep(5)

humidity = Humidity(pin_dht=18)

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "OLFA/BROYEUR",
    watchdog=100,
    sysinfo_period = 600,
    led_wifi='LED',
    name = "Broyeur",
    logging_level=logging.INFO,
    device=humidity
    )

iot.run()