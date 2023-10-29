
import time
import uasyncio as asyncio
from machine import Pin
from fmpyiot.fmpyiot import FmPyIot
from fmpyiot.topics import Topic, TopicRoutine, TopicIrq


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

async def calc(topic, payload=None):
    payload = payload or 42
    print(f"calc({topic},{payload})")
    l=await asyncio.gather(long_calculus(topic, payload), short_calculus(topic, payload))
    print(f"Result des calculs : {l}")
    return sum(l)

# Un topic mode synchrone (pas la peine pour allumer une led)
topic_led = Topic("./LED", action = lambda topic, payload: led(int(payload)))
iot.add_topic(topic_led)

# Topics en asynchone
topic_blink_led = Topic("./LED_BLINK", action = blink_led)
iot.add_topic(topic_blink_led)

# A la fois vrai Topic (qui est activé par reception MQTT) et routine (qui est activé toutes les x secondes)
topic_calc = Topic("./calc", read = calc, send_period=5)
iot.add_topic(topic_calc)


# Des routines sans aucun topic
async def routine_blink():
    while True:
        await asyncio.sleep(10)
        print("Routine : blink on!")
        await iot.publish_async("./LED_BLINK",1)
        await asyncio.sleep(5)
        print("Routine : blink off!")
        await iot.publish_async("./LED_BLINK",0)
topic_routine_blink = TopicRoutine(routine_blink)
iot.add_routine(topic_routine_blink)

#Une detection de changement d'état sur une Pin
iot.add_topic(TopicIrq("./LED", pin=Pin(15,Pin.IN), trigger = Pin.IRQ_RISING, values=("1","0")))


iot.run()