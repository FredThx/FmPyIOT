from devices.ds18b20 import DS18b20
from devices.fdht import DHT22
from devices.fluxldr import LuxLDR
from machine import Pin, ADC

from fmpyiot.fmpyiot_sleep import FmPyIotSleep
from fmpyiot.topics import Topic
import time

print("BOOT")
for i in range(5):
    time.sleep(1)
    print(".",end="")

iot = FmPyIotSleep(
    mqtt_host = "***REMOVED***",
    mqtt_base_topic = "T-HOME/SERRE",
    ssid = 'WIFI_THOME2',
    password = "***REMOVED***",
    watchdog=None,
    sleep_period = 1200, # secondes
    run_pin=22,
    led_wifi='LED',
    )                                                                                                                       

ds = DS18b20(14)
dht = DHT22(16)
ldr = LuxLDR(channel = 2, R= 10_000, k=0.9, Rp=4_700, vcc=5, adc_ref=3.3) #Channel2 = ADC2 = GPIO28
adc_bat = ADC(Pin(27,mode = Pin.IN))

temperature = Topic("./temperatures", read=lambda topic, payload : ds.read_all_async(), send_period=1)
humidity = Topic("./humidity", read = lambda topic, payload : dht.read_humidity(), send_period=1)
luminosite = Topic("./luminosite", read = lambda topic, payload : ldr.read(), send_period=1)
voltage = Topic("./bat_voltage", read = lambda topic, payload : adc_bat.read_u16()*3.3/65535/0.6+0.165, send_period=1)

iot.add_topic(temperature)
iot.add_topic(humidity)
iot.add_topic(luminosite)
iot.add_topic(voltage)
iot.run()