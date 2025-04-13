import logging, json
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicRoutine
from devices.ds18b20 import DS18b20
from machine import Pin
import dht
import uasyncio as asyncio
from credentials import CREDENTIALS

class Humidity:
    params = {
        }
    params_json = "params.json"
    
    def __init__(self, 
                 dht_pins:list[int]=None,
                 ):
        self.dhts = [dht.DHT22(Pin(pin)) for pin in dht_pins] if dht_pins else []
        self.load_params()
    
    def set_iot(self, iot:FmPyIotWeb):
        self.iot = iot
        #self.iot.set_param('impregnation', default=self.params, on_change=self.load_params)
        for i, dht in enumerate(self.dhts):
            self.iot.add_topic(Topic(f"./humidity{i}", read=dht.humidity, send_period=2))
            self.iot.add_topic(Topic(f"./temperature{i}", read=dht.temperature, send_period=2))
        self.iot.add_topic(TopicRoutine(action=self.measure, send_period=2, topic=f"./measure{i}"))


    async def measure(self):
        '''Mesure l'humidité et la température
        '''
        for dht in self.dhts:
            try:
                dht.measure()
                asyncio.sleep_ms(1) # pour éviter de faire trop de mesure en même temps
            except OSError as e:
                logging.error(f"Error on dht.measure() : {e}")


    #TODO : incoprporer ce code à la classe FmPyIotWeb
    def _load_params(self, params:dict):
        '''Load les paramètres à partir d'un dict
        en vérifiant le typage
        '''
        for k,v in params.items():
            if k in self.params:
                try:
                    self.params[k] = type(self.params[k])(v) # type cast idem self.params
                except ValueError:
                    logging.error(f"Error with {k} : {v} cannot be converted to {type(self.params[k])}")
            else:
                logging.warning(f"Param {k} not in params")


    def load_params(self, params:dict=None):
        '''Initialise les paramètres
            - a partir d'un fichier json
            - ou d'un dict en entrée 
        '''
        if params:
            self._load_params(params)
        else:
            try:
                with open(self.params_json,"r") as json_file:
                    self._load_params(json.load(json_file))
            except OSError as e:
                logging.error(str(e))
        print(f"Params loaded. New params : {self.params}")

    
humidity = Humidity(dht_pins=[26, 22])

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "OLFA/IMPREGNATION/IR",
    watchdog=100,
    sysinfo_period = 600,
    led_wifi="LED",
    web=True,
    name = "machine imprégnation IR",
    logging_level=logging.INFO,
    )

humidity.set_iot(iot)

iot.run(wait = 5)

