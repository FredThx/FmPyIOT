
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import TopicAction
import logging
from devices.servo import Servo
from devices.bargraph import BarGraph, BarGraphPWM
from afficheur_wc import AfficheurWC
import json
from credentials import CREDENTIALS

time.sleep(5)

assert len([])==0, "Error with len!"

afficheur_wc = AfficheurWC(
    servo=Servo(28),
    bargraph=BarGraphPWM([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
)

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/WC/PORTE",
    watchdog=None,
    sysinfo_period = 600,
    led_wifi='LED',
    web=True,
    name = "AFFICHEUR WC",
    render_web=afficheur_wc.render_web,
    logging_level=logging.DEBUG,
    )

afficheur_wc.set_iot(iot)
iot.run()