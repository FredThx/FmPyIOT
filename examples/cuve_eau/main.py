from machine import I2C, Pin
from devices.lidar import TF_Luna
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic
import logging
from credentials import CREDENTIALS

i2c = I2C(0, scl=Pin(13), sda=Pin(12), freq = 400_000)
lidar = TF_Luna(i2c, min=20, max=800, freq = 100)

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    mqtt_base_topic = "OLFA/ETANG_HAUT/NIVEAU",
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    watchdog=300,
    sysinfo_period = 600,
    led_wifi='LED',
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    name = "La hauteur de l'étang du HAUT",
    logging_level=logging.INFO,
    )


def get_distance():
    try:
        return lidar.distance()
    except OSError:
        return "Erreur capteur lidar"

distance = Topic("./distance", read=lambda topic, payload : get_distance(), send_period=10)
iot.add_topic(distance)
iot.run()