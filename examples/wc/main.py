
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import TopicAction
import logging
from devices.servo import Servo
from devices.baregraph import BareGraph

from credentials import CREDENTIALS

time.sleep(5)

assert len([])==0, "Error with len!"

servo = Servo(28)
bargraph = BareGraph([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

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
    logging_level=logging.DEBUG,
    )

def set_etat(payload):
    if payload == 'libre':
        servo.move(170-90) 
    else:
        servo.move(170)
#TODO : parametres à ajuster pour le servo : speed et angles
iot.add_topic(TopicAction("./ETAT", lambda topic, payload: set_etat(payload)))
iot.add_topic(TopicAction("./BARGRAPH", lambda topic, payload: bargraph.set_level(int(payload))))

iot.run()