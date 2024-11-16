
import time
from machine import I2C, Pin
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import TopicAction, TopicRead
import logging
from devices.lidar import TF_Luna

from credentials import CREDENTIALS

time.sleep(5)

class CuveFuel:
    params = {
        'lidar_min' : 20,
        'lidar_max' : 800,
        'lidar_freq' : 100
    }
    def __init__(self):
        self.i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq = 400_000)
        self.lidar = TF_Luna(self.i2c, min=20, max=800, freq = 100)
        self.leds = {
            'rouge' : Pin(1, Pin.OUT),
            'vert' : Pin(0,Pin.OUT)
            }
    def read_distance(self, *args, **kwargs):
        return self.lidar.distance()

    def set_leds(self, payload:str):
        logging.info(f"Set led = '{payload}'")
        for key, led in self.leds.items():
            if key == payload:
                led.on()
            else:
                led.off()

    def load_params(self, param:dict):
        logging.info(f"cuve_fuel.load_params({param})")
        self.lidar = TF_Luna(self.i2c,
                            min=int(param['lidar_min']),
                            max=int(param['lidar_max']),
                            freq = int(param['lidar_freq']))

cuve_fuel = CuveFuel()

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/CUVE-FUEL2",
    watchdog=100,
    sysinfo_period = 600,
    led_wifi='LED',
    name = "Cuve de Fuel",
    logging_level=logging.INFO,
    )


iot.add_topic(TopicRead("./distance", read= cuve_fuel.read_distance, send_period=10))
iot.add_topic(TopicAction("./LED", action = lambda topic, payload : cuve_fuel.set_leds(payload)))
iot.set_param('cuve_fuel', default=cuve_fuel.params, on_change=cuve_fuel.load_params)


iot.run()