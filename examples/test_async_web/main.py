
import time
import uasyncio as asyncio
from machine import Pin
from fmpyiot.fmpyiot import FmPyIot
from fmpyiot.topics import Topic, TopicRoutine, TopicIrq, TopicOnChange


time.sleep(5)


iot = FmPyIot(
    mqtt_host = "***REMOVED***",
    mqtt_base_topic = "T-HOME/TEST",
    ssid = 'WIFI_THOME2',
    password = "***REMOVED***",
    watchdog=None,
    sysinfo_period = 600,
    #led_wifi='LED',
    web=True
    )

led = Pin('LED')

topic_led = Topic("./LED", action = lambda topic, payload: led(int(payload)))
iot.add_topic(topic_led)

#Une detection de changement d'état sur une Pin
iot.add_topic(TopicIrq("./LED", pin=Pin(15,Pin.IN), trigger = Pin.IRQ_RISING, values=("1","0")))


@iot.web.route("/")
async def hello(request):
    await request.write("HTTP/1.1 200 OK\r\n\r\n")
    await request.write("Hello")

iot.run()