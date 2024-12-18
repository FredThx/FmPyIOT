from devices.ds18b20 import DS18b20
from devices.fdht import DHT22
from devices.fluxldr import LuxLDR
from machine import Pin
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic

from credentials import CREDENTIALS

ds = DS18b20(14)
dht = DHT22(16)
ldr = LuxLDR(channel = 0, R= 10_000, k=0.9) #Channel0 = ADC0 = GPIO26
led = Pin(17,Pin.OUT)

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/SERRE",
    watchdog=100,
    sysinfo_period = 600,
    name="Serre de Fred",
    description="Une petite serre pour des salades.",
    )

temperature = Topic("./temperatures", read=lambda topic, payload : ds.read_all_async(), send_period=60)
humidity = Topic("./humidity", read = lambda topic, payload : dht.read_humidity(), send_period=60)
luminosite = Topic("./luminosite", read = lambda topic, payload : ldr.read(), send_period=60)
led_topic = Topic('./LED', action = lambda payload : led.value(int(payload)))


iot.add_topic(temperature)
iot.add_topic(humidity)
iot.add_topic(luminosite)
iot.add_topic(led_topic)
iot.run()