from machine import I2C, Pin
import utime
import sys
from devices.lidar import TF_Luna

from fmpyiot.fmpyiot import FmPyIot
from fmpyiot.topics import Topic

i2c = I2C(0, scl=Pin(13), sda=Pin(12), freq = 400_000)
lidar = TF_Luna(i2c, min=20, max=800, freq = 100)

iot = FmPyIot(            
    mqtt_host = "192.168.0.11",
    mqtt_base_topic = "OLFA/VAPEUR/CUVE_ETANG",
    ssid = 'OLFA_PRODUCTION',
    password = "79073028",
    #ssid = 'OLFA_WIFI',
    #password = "Olfa08SignyLePetit",
    watchdog=100,
    sysinfo_period = 600,
    async_mode=False)

distance = Topic("./distance", read=lambda topic, payload : lidar.distance(), send_period=10)

if True:
    while not iot.connect():
        print("Erreur lors de la connexion.... en retente!")
    iot.add_topic(distance)
    iot.run()