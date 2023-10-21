from machine import Pin
import time
from fmpyiot.fmpyiot_2 import FmPyIot
from fmpyiot.topics import Topic

detecteur = Pin(15,Pin.IN)

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

      
detection_topic = Topic("./detect", send_period= 5, read=lambda topic, payload : detecteur())
test_incoming_topic = Topic("./mqtt_async_in", action = lambda topic, payload : print(f"Le test {topic} est ok : {payload}"))


iot.add_topic(detection_topic)
iot.add_topic(test_incoming_topic)

#iot.run()
