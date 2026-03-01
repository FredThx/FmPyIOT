from machine import Pin
import time, logging
from fmpyiot.fmpyiot_web import FmPyIotWeb
from detector import Detector
from credentials import CREDENTIALS

time.sleep(5)

detector = Detector(pin_detector=27, output_topic="T-HOME/COULOIR_HAUT/ECLAIRAGE/relais2")

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/COULOIR_HAUT/DETECT",
    watchdog=100,
    sysinfo_period = 600,
    led_wifi='LED',
    name = "Detection couloir du haut",
    logging_level=logging.INFO,
    device=detector
    )

iot.run()
