from machine import Pin, SPI
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
from devices.manometre import ManoAnalog
import sh1107
from manometre import Manometre
import logging

time.sleep(5)

spi1 = SPI(1, baudrate=1_000_000, sck=Pin(10), mosi=Pin(11), miso=Pin(8))
display = sh1107.SH1107_SPI(128, 64, spi1, Pin(8), Pin(12), Pin(9), rotate=0)
key0 = Pin(15, Pin.IN)
mano = ManoAnalog(Pin(28), max_psi=150, min_voltage=0.317, no_negative = True)

device = Manometre(display, key0, mano, name="MANOMETRE_INCENDIE")

iot = FmPyIotWeb(
    mqtt_host = "192.168.0.20",
    mqtt_base_topic = "OLFA/INCENDIE",
    ssid = 'OLFA_PRODUCTION',
    password = "79073028",
    watchdog=300,
    sysinfo_period = 600,
    led_wifi='LED',
    web_credentials=("Fred", "eric"),
    name = "La pression du réseau incendie",
    logging_level=logging.INFO,
    on_fail_connect=device.display_connect,
    device=device,
    )

iot.run()
