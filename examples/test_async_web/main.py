
import time
import uasyncio as asyncio
from machine import Pin
from fmpyiot.fmpyiot_2 import FmPyIot
from fmpyiot.topics import Topic


time.sleep(5)


iot = FmPyIot(
    mqtt_host = "***REMOVED***",
    mqtt_base_topic = "T-HOME/TEST",
    ssid = 'WIFI_THOME2',
    password = "***REMOVED***",
    watchdog=None,
    sysinfo_period = 600,
    #led_wifi='LED',
    )

led = Pin('LED')
led_blink = False

async def set_led(_, val):
    global led
    print(f"set_led({val})")
    led(int(val))
    print(f"led({led()})")
    await asyncio.sleep_ms(10)

async def blink_led(_,val):
    print(f"Blink = {val}")
    global led_blink
    global led
    led_blink = int(val)==1
    while led_blink:
        led.on()
        await asyncio.sleep_ms(300)
        led.off()
        await asyncio.sleep(1)

async def long_calculus(topic, payload):
    await asyncio.sleep(10)
    return int(payload)+1

topic_led = Topic("./LED", action = set_led)
topic_blink_led = Topic("./LED_BLINK", action = blink_led)
topic_long_calculus = Topic("./calc", read = long_calculus)

iot.add_topic(topic_led)
iot.add_topic(topic_blink_led)
iot.add_topic(topic_long_calculus)

iot.run()