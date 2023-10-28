
import time
import uasyncio as asyncio
from machine import Pin
from fmpyiot.fmpyiot_2 import FmPyIot
from fmpyiot.topics import Topic, TopicRoutine


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
    return f"Led is {val}"

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
    print("start long calculus")
    await asyncio.sleep(10)
    print("long calculus done")
    return int(payload)+1

async def short_calculus(topic, payload):
    print("start short calculus")
    await asyncio.sleep_ms(50)
    print("short calculus done")
    return int(payload)**2

async def calc(topic, payload):
    l=await asyncio.gather(long_calculus(topic, payload), short_calculus(topic, payload))
    print(f"Result des calculs : {l}")
    return sum(l)

topic_led = Topic("./LED", action = set_led, reverse_topic = True)
topic_blink_led = Topic("./LED_BLINK", action = blink_led)
topic_calc = Topic("./calc", read = calc)

iot.add_topic(topic_led)
iot.add_topic(topic_blink_led)
iot.add_topic(topic_calc)


async def routine():
    while True:
        await asyncio.sleep(10)
        print("Routine : blink on!")
        await iot.a_publish("./LED_BLINK",1)
        await asyncio.sleep(5)
        print("Routine : blink off!")
        await iot.a_publish("./LED_BLINK",0)

iot.add_routine(TopicRoutine(routine))

iot.run()