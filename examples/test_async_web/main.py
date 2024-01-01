
import time
import uasyncio as asyncio
from machine import Pin, ADC
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicAction, TopicRoutine, TopicIrq, TopicOnChange, TopicRead
import logging

time.sleep(5)


iot = FmPyIotWeb(
    mqtt_host = "***REMOVED***",
    mqtt_base_topic = "T-HOME/TEST",
    ssid = 'WIFI_THOME2',
    password = "***REMOVED***",
    watchdog=None,
    sysinfo_period = 600,
    #led_wifi='LED',
    web=True,
    web_credentials=(***REMOVED***, ***REMOVED***),
    name = "FmPyIot TEST",
    logging_level=logging.INFO,
    )

led = Pin('LED')

iot.add_topic(TopicAction("./LED", lambda topic, payload: led(not led())))
iot.add_topic(TopicRead("./voltage", lambda topic, payload : ADC(Pin(29)).read_u16()/65535*3.3, send_period=20, reverse_topic="./get_voltage"))
#Une detection de changement
#  d'état sur une Pin
iot.add_topic(TopicIrq("./LED", pin=Pin(16,Pin.IN), trigger = Pin.IRQ_RISING, values=("1","0")))


## Des routines

### A partir d'une routine infinie
leds = [Pin(i,Pin.OUT) for i in range(0,16)]
index_leds = 0
async def run_leds():
    while True:
        global leds
        global index_leds
        leds[index_leds].value(0)
        index_leds = (index_leds+1)%len(leds)
        leds[index_leds].value(1)
        await asyncio.sleep(0.1)
iot.add_topic(TopicRoutine(run_leds))

### A partir d'une function et d'une période
leds2 = [Pin(i,Pin.OUT) for i in range(17,22)]
index_leds2 = 0
def run_leds2():
    global leds2
    global index_leds2
    leds2[index_leds2].value(0)
    index_leds2 = (index_leds2+1)%len(leds2)
    leds2[index_leds2].value(1)
iot.add_topic(TopicRoutine(run_leds2,send_period=0.05))




iot.run()