
import time
from machine import Pin

time.sleep(5)

from croquettes import Croquettes
from fmpyiot.fmpyiot import FmPyIot
from fmpyiot.topics import Topic

croquettes = Croquettes(Pin(13),Pin(12),Pin(7), Pin(8), Pin(6))
iot = FmPyIot(            
    mqtt_host = "***REMOVED***",
    mqtt_base_topic = "T-HOME/CROQ3",
    ssid = 'WIFI_THOME2',
    password = "***REMOVED***",
    watchdog=300,
    sysinfo_period = 600)


balance = Topic("./POIDS", read=croquettes.get_weight, send_period=20)
dose = Topic("./DOSE", action = lambda topic, payload : croquettes.distribute(float(payload)))

def ftest():
    time.sleep(2)
    return iot.lock_timer

test = Topic("./TEST", read = ftest, send_period=1)

if True:
    if iot.connect():
        iot.add_topic(balance)
        iot.add_topic(dose)
        #iot.add_topic(test)
else:
    iot.wlan.connect(iot.ssid, iot.password)
    while True:
        print(iot.str_network_status())
        time.sleep(0.1)