
import time
from machine import Pin
from croquettes import Croquettes
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicAction
import logging
time.sleep(5)

from credentials import CREDENTIALS

croquettes = Croquettes(
        hx_clk= Pin(13), # GP13 = 17
        hx_data= Pin(12), # GP12 = 16
        motor_pinA= Pin(7), # GP7 = 10
        motor_pinB= Pin(8), # GP8 = 11
        motor_pin_ena= Pin(6), # GP6 = 9
        vibreur_pinA= Pin(14), # GP14 = 19
        vibreur_pinB= Pin(15), #GP15 = 20
        vibreur_ena= Pin(16), #GP16 = 21
        )

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/CROQ3",
    watchdog=300,
    sysinfo_period = 600,
    led_wifi='LED',
    name = "Les croquettes du futur des chats",
    logging_level=logging.INFO,
    )

iot.add_topic(Topic("./POIDS", read=croquettes.get_weight, send_period=20))
iot.add_topic(Topic("./DOSE", action = lambda topic, payload : croquettes.distribute_async(float(payload))))
iot.add_topic(Topic("./MOTOR", action = lambda topic, payload : croquettes.run_motor(float(payload))))
iot.add_topic(TopicAction('./VIBRE', lambda topic, payload: croquettes.vibre_async(float(payload))))

iot.set_param("croquettes", default=croquettes.params, on_change=croquettes.load_params)

iot.run()