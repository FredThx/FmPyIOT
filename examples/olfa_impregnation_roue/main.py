import logging
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic
from devices.ds18b20 import DS18b20
from machine import Pin
from credentials import CREDENTIALS
from roue import Roue
    
roue = Roue(
    out_A_pin=15,
    output_pin=6,
    out_B_pin=None,
    resolution=1,
    sub_topic="./distance",
)

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "OLFA/IMPREGNATION/IR",
    watchdog=100,
    sysinfo_period = 600,
    led_wifi="LED",
    web=True,
    name = "Coupe machine Infra-rouge",
    logging_level=logging.INFO,
    )

roue.set_iot(iot)

iot.run(wait = 5)