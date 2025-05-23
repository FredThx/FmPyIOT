from machine import Pin, I2C
import time, logging, uasyncio as asyncio
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicIrq, TopicAction
from devices.bmp280 import BMP280
from devices.ds18b20 import DS18b20
from devices import sh1106
from devices.display import Display, Field, Icon, RIGHT, LEFT, BarGraph
from credentials import CREDENTIALS

class Salon:
    
    def __init__(self):
        self.i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400_000)
        self.bmp = BMP280(self.i2c)
        self.ds = DS18b20(27)
        self.detecteur = Pin(26)
        self.display = Display(sh1106.SH1106_I2C(128, 64, self.i2c, addr=60, rotate=0, delay=0))
        self.display.set_widget("heure", Field("", row=0,column=1,width=8, align=RIGHT))
        self.display.set_widget("T-HOME/SALON/ECRAN/PRESSION", Field("P=", row=2,column=0,width=4, align=RIGHT, unit=" hPa"), "???")
        self.display.set_widget("T-HOME/SALON/ECRAN/temperature", Field("T=", row=4,column=0, width=4, align=RIGHT, unit = " C"), "???")
        self.display.set_widget("T-HOME/CUVE-FUEL/quantite", BarGraph(12*8,0, lenght=50, width=8, max_value=1500, orient=90))
        self.display.set_widget("T-HOME/CUVE-FUEL/quantite", Field("", row=7,column=10, width=4, align=RIGHT, unit=' l'),"???")
        self.display.set_widget("T-HOME/SALON/ECRAN/PRESSION_VARIATION", Icon(9*8+2, 16,
                icons={
                    "UP" : self.icon_up,
                    "EQ" : self.icon_eq,
                    "DOWN" : self.icon_down
                }
                                                                        ))
        self.params = {
            'pressure_offset' : 0,
            'temperature_offset' : 0
        }

    icon_up = [[0,0,0,1,1,0,0,0],
               [0,0,1,1,1,1,0,0],
               [0,1,1,1,1,1,1,0],
               [1,1,0,1,1,0,1,1],
               [1,0,0,1,1,0,0,1],
               [0,0,0,1,1,0,0,0],
               [0,0,0,1,1,0,0,0],
               [0,0,0,1,1,0,0,0],]
    
    icon_eq = [[0,0,0,0,0,0,0,0],
               [1,1,1,1,1,1,1,1],
               [1,1,1,1,1,1,1,1],
               [0,0,0,0,0,0,0,0],
               [0,0,0,0,0,0,0,0],
               [1,1,1,1,1,1,1,1],
               [1,1,1,1,1,1,1,1],
               [0,0,0,0,0,0,0,0],
               ]
    @property
    def icon_down(self):
        return reversed(self.icon_up)

    @staticmethod
    def get_cuve_icon(payload:str):
        width, height = 60, 24
        try:
            niveau = int(payload) // int(1500/height)
        except TypeError:
            niveau = 0
        haut_bas = [0,1] + [1]*(width-4) + [1,0]
        icon = [haut_bas]
        icon += [[1]*width if _niveau <= niveau else [1] + [0]*(width-2) + [1] for _niveau in range(height,0,-1)]
        icon += [haut_bas]
        return icon

    def get_pressure(self, **kwargs):
        return int(self.bmp.pressure/100 - float(self.params['pressure_offset']))
    
    async def get_temperature(self, **kwargs):
        raw_temp = await self.ds.read_async()
        return raw_temp + float(self.params['temperature_offset'])

    def load_params(self, param:dict):
        logging.info("SALON : LOAD PARAMS")
        self.params.update(param)
    
    async def show_time(self):
        #Une routine qui affiche l'heure
        s0 = 0
        while True:
            _, _, _, _, h, m, s, _ = iot.rtc.datetime()
            if s0!=s:
                self.display.set("heure", f"{h:02}:{m:02}:{s:02}")
                s0=s
            await asyncio.sleep_ms(100)
    

salon = Salon()

time.sleep(5)

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/SALON/ECRAN",
    watchdog=100,
    sysinfo_period = 600,
    led_incoming="LED", #internal
    led_wifi=16,
    web=True,
    name = "Salon",
    logging_level=logging.INFO,
    )

iot.set_param('salon', default=salon.params, on_change=salon.load_params)

def on_irq(topic, payload):
    logging.info(f"salon.display.power({payload})")
    salon.display.power(payload)

detection_topic = TopicIrq("./detect",
                           pin=salon.detecteur,
                           trigger = Pin.IRQ_RISING + Pin.IRQ_FALLING,
                           tempo_after_falling=10.0,
                           #on_irq=lambda topic, payload : salon.display.power(payload))
                           on_irq=on_irq)
topic_pression = Topic("./PRESSION",
                       read=salon.get_pressure,
                       send_period=30,
                       on_incoming=salon.display.set)
topic_temperature = Topic("./temperature",
                          read=salon.get_temperature,
                          send_period=30,
                          on_incoming=salon.display.set)

topic_fioul = TopicAction("T-HOME/CUVE-FUEL/quantite",action=salon.display.set)
topic_pression_variation = TopicAction("T-HOME/SALON/PRESSION_VARIATION", action=salon.display.set)

iot.add_topic(topic_pression)
iot.add_topic(topic_temperature)
iot.add_topic(detection_topic)
iot.add_topic(topic_fioul)
iot.add_topic(topic_pression_variation)
iot.add_routine(salon.show_time)

iot.run()

