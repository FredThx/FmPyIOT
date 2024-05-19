from devices.ds18b20 import DS18b20
from devices.fdht import DHT22
from devices.fluxldr import LuxLDR
import machine
import time

print("BOOT")
for i in range(5):
    time.sleep(1)
    print(".",end="")

print(f"reset_cause : {machine.reset_cause()}")

alim_pin = machine.Pin(26)
alim_pin.init(machine.Pin.OUT,value = 1)
time.sleep(0.5)

ds = DS18b20(14)
dht = DHT22(16)
ldr = LuxLDR(channel = 0, R= 10_000, k=0.9) #Channel0 = ADC0 = GPIO26


while True:
    alim_pin(1)
    print(f"température (ds): {ds.read()}")
    print(f"Température (dht) = {dht.read_temperature()}")
    time.sleep(0.1)
    print(f"Humidité = {dht.read_humidity()}")
    
    print("sleep for 10 seconds...")
    alim_pin(0)
    time.sleep(0.3)
    machine.lightsleep(10_000)
    print("en light sleep")
    time.sleep(2)