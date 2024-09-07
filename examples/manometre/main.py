from machine import Pin, SPI
import sh1107
from fonts.font_56 import font_56
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicRoutine, TopicIrq
from devices.manometre import ManoAnalog
import uasyncio as asyncio
import logging
time.sleep(5)

spi1 = SPI(1, baudrate=1_000_000, sck=Pin(10), mosi=Pin(11), miso=Pin(8))
display = sh1107.SH1107_SPI(128, 64, spi1, Pin(8), Pin(12), Pin(9), rotate=0)

trys = 1
def display_connect():
    global trys, iot
    display.fill(0)
    display.text(iot.mqtt_base_topic,0,5,1)
    display.text("Connection a ",5,20,1)
    display.text(iot.client.server,15,35,1)
    display.text(f"Tentative {trys}", 0, 55, 1)
    trys += 1
    display.show()


key0 = Pin(15, Pin.IN)
mano = ManoAnalog(Pin(28), max_psi=150, min_voltage=0.317, no_negative = True)

iot = FmPyIotWeb(
    mqtt_host = "192.168.0.11",
    mqtt_base_topic = "OLFA/INCENDIE",
    ssid = 'WIFI_THOME2',
    password = "***REMOVED***",
    watchdog=300,
    sysinfo_period = 600,
    led_wifi='LED',
    web_credentials=(***REMOVED***, ***REMOVED***),
    name = "La pression du réseau incendie",
    logging_level=logging.INFO,
    on_fail_connect=display_connect
    )


def show_pressure():
    global power_display_runners
    pression= mano.read()
    display.fill(1)
    font_56.text(display, f"{pression:0.1f}{'😀' if pression >3 else '🙁'}",0,0)
    display.show()
    if pression < 3:
        display.poweron()
    elif power_display_runners ==0:
        display.poweroff()

power_display_runners = 0
async def power_display():
    global power_display_runners
    display.poweron()
    power_display_runners += 1
    await asyncio.sleep(10)
    power_display_runners -= 1
    if power_display_runners<1:
        display.poweroff()

# Topic pour envoie de la pression via MQTT
iot.add_topic(Topic("./PRESSION", read=mano.read, send_period=20))
# Routine pour mise à jour de l'ecran
iot.add_topic(TopicRoutine(show_pressure, send_period=1))
# Routine pour on_off de l'ecran selon bouton key0
iot.add_topic(TopicIrq("./KEY0", pin=key0, trigger = Pin.IRQ_RISING, action=power_display))
iot.add_routine(TopicRoutine(power_display))

display_connect()
iot.run()
