from machine import Pin
import time
from fmpyiot.fmpyiot_2 import FmPyIot
from fmpyiot.topics import Topic, TopicIrq

detecteur = Pin(15,Pin.IN)

time.sleep(5)

iot = FmPyIot(            
    mqtt_host = "***REMOVED***",
    mqtt_base_topic = "T-HOME/BUREAU/DETECTION",
    ssid = 'WIFI_THOME2',
    password = "***REMOVED***",
    watchdog=100,
    sysinfo_period = 600,
    led_incoming="LED", #internal
    led_wifi=16
    )

compteur = 0
def get_compteur():
    global compteur
    compteur += 1
    return compteur

compteur_topic = Topic("./compteur", send_period= 10, read=get_compteur)
test_incoming_topic = Topic("./mqtt_async_in", action = lambda topic, payload : print(f"Le test {topic} est ok : {payload}"))

detection_topic = TopicIrq("./detect", pin=detecteur, trigger = Pin.IRQ_RISING , values=("NO", "DETECT"),)


iot.add_topic(compteur_topic)
iot.add_topic(test_incoming_topic)
iot.add_topic(detection_topic)
iot.run()
