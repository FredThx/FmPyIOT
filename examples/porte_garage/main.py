# main.py -- put your code here!


from machine import Pin
import time
from fmpyiot.fmpyiot import FmPyIot
from fmpyiot.topics import Topic
from porte_garage import PorteGarage

porte_garage = PorteGarage(
    sensor_close = Pin(21),
    sensor_open = Pin(20),
    gate_motor_push = Pin(19))

iot = FmPyIot(            
    mqtt_host = "***REMOVED***",
    mqtt_base_topic = "T-HOME/GARAGE/PORTE",
    ssid = 'WIFI_THOME2',
    password = "***REMOVED***",
    watchdog=100,
    sysinfo_period = 600,
    async_mode=False)

      
gate_state_topic = Topic("./etat", read=lambda topic, payload : porte_garage.get_gate_state(), send_period=5)
motor_topic = Topic('./push', action = lambda payload : porte_garage.push_button())


if True:
    while not iot.connect():
        print("Erreur lors de la connexion.... en retente!")
    iot.add_topic(gate_state_topic)
    iot.add_topic(motor_topic)
    iot.run()
