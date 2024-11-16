
import time, json
import uasyncio as asyncio
from machine import Pin, ADC, SPI, RTC
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicAction, TopicRoutine, TopicIrq, TopicOnChange, TopicRead
import logging
from lcd12864 import SPI_LCD12864
from devices.display import Display, Field, RIGHT, Icon

from credentials import CREDENTIALS

time.sleep(5)
try:
    del len #Bug micropython!!!
except:
    pass

assert len([])==0, "Error with len!"

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
    logging_level=logging.DEBUG,
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

### A partir d'une function async pas infinie et d'une période
async def run_leds_once():
    global leds
    for i in range(len(leds)-1,-1,-1):
        leds[i].value(1)
        await asyncio.sleep(0.1)
        leds[i].value(0)

iot.add_topic(TopicRoutine(run_leds_once, send_period=5))

#Un ecran
lcd = SPI_LCD12864(
        spi=SPI(0, polarity=0, phase = 1,bits=8, sck=Pin(6), mosi=Pin(7)),
        cs=Pin(5, Pin.OUT, value = 0)
    )

lcd.rect(0,0,128,64,1)
lcd.rect(3,3,128-6,64-6,1)
lcd.update()

HEART_ICONS = [
    [
        [0,0,0,0,0,0,0,0,0,0,0],
        [0,0,1,1,1,0,1,1,1,0,0],
        [0,1,1,0,1,1,1,1,1,1,0],
        [0,1,0,1,1,1,1,1,1,1,0],
        [0,1,1,1,1,1,1,1,1,1,0],
        [0,0,1,1,1,1,1,1,1,0,0],
        [0,0,0,1,1,1,1,1,0,0,0],
        [0,0,0,0,1,1,1,0,0,0,0],
        [0,0,0,0,0,1,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0] ],
    [
        [0,0,1,1,0,0,0,1,1,0,0],
        [0,1,1,1,1,0,1,1,1,1,0],
        [1,1,1,0,1,1,1,1,1,1,1],
        [1,1,0,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1],
        [0,1,1,1,1,1,1,1,1,1,0],
        [0,0,1,1,1,1,1,1,1,0,0],
        [0,0,0,1,1,1,1,1,0,0,0],
        [0,0,0,0,1,1,1,0,0,0,0],
        [0,0,0,0,0,1,0,0,0,0,0] ],
  ]

def draw_icon( lcd, from_x, from_y, icon ):
    for y, row in enumerate( icon ):
        for x, color in enumerate( row ):
            if color==None:
                continue
            lcd.pixel( from_x+x,
                       from_y+y,
                       color )

async def heart_async():
    while True:
        for i in range(len(HEART_ICONS)):
            draw_icon(lcd, 1,1,HEART_ICONS[i])
            lcd.update()
            await asyncio.sleep(0.5)

iot.add_topic(TopicRoutine(heart_async))

def draw_text(lcd, payload):
    payload = json.loads(payload)
    print(f"payload = {payload} type = {type(payload)}")
    lcd.text(payload['text'], payload['x'],payload['y'],1)
    lcd.update()

iot.add_topic(TopicAction("./text", lambda _topic, payload : draw_text(lcd, payload)))

#####
# Utilisation Display
#####

disp = Display(lcd)
disp.set_field("heure", Field("", 2,3,width=8, align=RIGHT))

#Une routine qui affiche l'heure
async def show_time():
    s0 = 0
    while True:
        _, _, _, _, h, m, s, _ = iot.rtc.datetime()
        if s0!=s:
            disp.set("heure", f"{h:02}:{m:02}:{s:02}")
            s0=s
        await asyncio.sleep_ms(100)
iot.add_routine(show_time)

#Liaison avec un topic MQTT entrant
disp.set_field("croq_status", Field("Croq.:", 4, 1, 7, invert=True))
iot.add_topic(TopicAction('./CROQ_STATUS', lambda topic, payload : disp.set("croq_status", payload)))

#Une icone selon message MQTT entrant
f_icon = Icon(10,43)
f_icon.set_icon("OFFLINE",[
                [0,0,0,1,1,1,1,1,0,0,0],
                [0,0,1,1,1,1,1,1,1,0,0],
                [0,1,1,0,0,1,0,0,1,1,0],
                [0,1,1,1,1,1,1,1,1,1,0],
                [1,1,1,1,1,1,1,1,1,1,1],
                [0,1,1,1,0,0,0,1,1,1,0],
                [0,0,1,0,1,1,1,0,1,0,0],
                [0,0,0,1,1,1,1,1,0,0,0]])
f_icon.set_icon("ONLINE",[
                [0,0,0,1,1,1,1,1,0,0,0],
                [0,0,1,1,1,1,1,1,1,0,0],
                [0,1,1,0,0,1,0,0,1,1,0],
                [0,1,1,1,1,1,1,1,1,1,0],
                [1,1,1,0,1,1,1,0,1,1,1],
                [0,1,1,1,0,0,0,1,1,1,0],
                [0,0,1,1,1,1,1,1,1,0,0],
                [0,0,0,1,1,1,1,1,0,0,0]])
disp.set_field("icon", f_icon)
iot.add_topic(TopicAction('./CROQ_STATUS', lambda topic, payload : disp.set("icon", payload)))

iot.set_param('blink_duration', default=1)

async def run_led_params():
    while True:
        try:
            duration = float(iot.get_param('blink_duration'))
        except Exception as e:
            print(e)
            await asyncio.sleep(0.1)        
        else:
            machine.Pin("LED").toggle()
            await asyncio.sleep(duration)        
iot.add_topic(TopicRoutine(run_led_params))


iot.run()