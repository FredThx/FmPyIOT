from devices.ds18b20 import DS18b20
from devices.fdht import DHT22
from devices.fluxldr import LuxLDR
from machine import Pin

from fmpyiot.fmpyiot import FmPyIot
from fmpyiot.topics import Topic

ds = DS18b20(14)
dht = DHT22(16)
ldr = LuxLDR(channel = 0, R= 10_000, k=0.9)
led = Pin(17,Pin.OUT)

iot = FmPyIot(            
    mqtt_host = "***REMOVED***",
    mqtt_base_topic = "T-HOME/SERRE",
    ssid = 'WIFI_THOME2',
    password = "***REMOVED***",
    watchdog=100,
    sysinfo_period = 600,
    web=True,
    name="Serre de Fred",
    description="Une petite serre pour des salades.",
    web_credentials=(***REMOVED***, ***REMOVED***),
    )

temperature = Topic("./temperatures", read=lambda topic, payload : ds.read_all(), send_period=60)
humidity = Topic("./humidity", read = lambda topic, payload : dht.read_humidity(), send_period=60)
luminosite = Topic("./luminosite", read = lambda topic, payload : ldr.read(), send_period=60)
led_topic = Topic('./LED', action = lambda payload : led.value(int(payload)))


iot.add_topic(temperature)
iot.add_topic(humidity)
iot.add_topic(luminosite)
iot.add_topic(led_topic)
iot.run()