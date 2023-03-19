
import time
from machine import Pin

time.sleep(5)

from croquettes import Croquettes
from fmpyiot.fmpyiot import FmPyIot
from fmpyiot.topics import Topic

croquettes = Croquettes(
        hx_clk = Pin(13), # GP13 = 17
        hx_data = Pin(12), # GP12 = 16
        motor_pinA = Pin(7), # GP7 = 10
        motor_pinB = Pin(8), # GP8 = 11
        motor_pin_ena = Pin(6) # GP6 = 9
        )

iot = FmPyIot(
    mqtt_host = "***REMOVED***",
    mqtt_base_topic = "T-HOME/CROQ3",
    ssid = 'WIFI_THOME2',
    password = "***REMOVED***",
    watchdog=300,
    sysinfo_period = 600,
    async_mode=False)


balance = Topic("./POIDS", read=croquettes.get_weight, send_period=20)
dose = Topic("./DOSE", action = lambda topic, payload : croquettes.distribute(float(payload)))

def ftest():
    time.sleep(2)
    return iot.lock_timer

test = Topic("./TEST", read = ftest, send_period=1)


if True:
    while not iot.connect():
        print("Erreur lors de la connexion.... en retente!")
    iot.add_topic(balance)
    iot.add_topic(dose)
    iot.run()