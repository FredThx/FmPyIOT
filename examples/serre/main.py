# main.py -- put your code here!


from ds18b20 import DS18b20
from fdht import DHT22
from fluxldr import LuxLDR


from fmpyiot.fmpyiot import *
from fmpyiot.topics import Topic

ds = DS18b20(14)
dht = DHT22(16)
ldr = LuxLDR(channel = 0, R= 10_000, k=0.9)

iot = FmPyIot(            
    mqtt_host = "192.168.10.150",
    mqtt_base_topic = "T-HOME/SERRE",
    ssid = 'WIFI_THOME2',
    password = "***REMOVED***",
    watchdog=None,
    sysinfo_period = 600,
    async_mode=False)

#iot.wd.disable()
temperature = Topic("./temperatures", read=ds.read_all, send_period=20)
humidity = Topic("./humidity", read = dht.read_humidity, send_period=20)
luminosite = Topic("./luminosite", read = ldr.read, send_period=20)

if True:
    while not iot.connect():
        print("Erreur lors de la connexion.... en retente!")
    iot.add_topic(temperature)
    iot.add_topic(humidity)
    iot.add_topic(luminosite)
    iot.run()
