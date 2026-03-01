
import time
import uasyncio as asyncio
from machine import Pin, ADC
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicAction, TopicRoutine, TopicIrq, TopicRead
import logging

from credentials import CREDENTIALS

time.sleep(5)

assert len([])==0, "Error with len!"

class Test:
    params = {'t1' : 1, 't2' : 1}

    def load_params(self, param:dict):
        logging.info("TEST : LOAD PARAMS")
        self.params.update(param)

test = Test()

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/TEST",
    watchdog=None,
    sysinfo_period = 600,
    #led_wifi='LED',
    web=True,
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
        await asyncio.sleep(float(test.params['t1']))
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

### A partir d'une function async pas infinie et d'une période
async def run_leds_once():
    global leds
    for i in range(len(leds)-1,-1,-1):
        leds[i].value(1)
        await asyncio.sleep(float(test.params['t2']))
        leds[i].value(0)

iot.set_param('test', default=test.params, on_change=test.load_params)

iot.add_topic(TopicRoutine(run_leds_once, send_period=5, topic='run leds once'))

iot.set_param('blink_duration', default=1)
led_blink = Pin(28, Pin.OUT)
async def run_led_params():
    while True:
        try:
            duration = float(iot.get_param('blink_duration'))
        except Exception as e:
            print(e)
            await asyncio.sleep(0.1)        
        else:
            led_blink.toggle()
            await asyncio.sleep(duration)        
iot.add_topic(TopicRoutine(run_led_params,send_period_as_param=False))


iot.run()