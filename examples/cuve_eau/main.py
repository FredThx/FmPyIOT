from machine import I2C, Pin
from devices.lidar import TF_Luna
from fmpyiot.fmpyiot import FmPyIot
from fmpyiot.topics import Topic

from credentials import CREDENTIALS

i2c = I2C(0, scl=Pin(13), sda=Pin(12), freq = 400_000)
lidar = TF_Luna(i2c, min=20, max=800, freq = 100)

iot = FmPyIot(            
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "OLFA/ETANG_HAUT/NIVEAU",
    watchdog=100,
    sysinfo_period = 600,
    async_mode=False)

def get_distance():
    try:
        return lidar.distance()
    except OSError:
        return "Erreur capteur lidar"

distance = Topic("./distance", read=lambda topic, payload : get_distance(), send_period=10)

if True:
    while not iot.connect():
        print("Erreur lors de la connexion.... on retente!")
    iot.add_topic(distance)
    iot.run()