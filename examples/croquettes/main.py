
import time
from machine import Pin
from croquettes import Croquettes
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic
import logging
time.sleep(5)

#TODO : faire une version async de Croquettes
# mais il va falloir gerer des locks!!

croquettes = Croquettes(
        hx_clk = Pin(13), # GP13 = 17
        hx_data = Pin(12), # GP12 = 16
        motor_pinA = Pin(7), # GP7 = 10
        motor_pinB = Pin(8), # GP8 = 11
        motor_pin_ena = Pin(6) # GP6 = 9
        )

iot = FmPyIotWeb(
    mqtt_host = "***REMOVED***",
    mqtt_base_topic = "T-HOME/CROQ3",
    ssid = 'WIFI_THOME2',
    password = "***REMOVED***",
    watchdog=300,
    sysinfo_period = 600,
    led_wifi='LED',
    web_credentials=(***REMOVED***, ***REMOVED***),
    name = "Les croquettes du futur des chats",
    logging_level=logging.INFO,
    )

balance = Topic("./POIDS", read=croquettes.get_weight, send_period=20)
dose = Topic("./DOSE", action = lambda topic, payload : croquettes.distribute(float(payload)))
motor = Topic("./MOTOR", action = lambda topic, payload : croquettes.run_motor(float(payload)))

iot.add_topic(balance)
iot.add_topic(dose)
iot.add_topic(motor)

iot.set_params_loader(croquettes.load_params)
iot.run()