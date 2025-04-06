import logging, json
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic
from devices.ds18b20 import DS18b20
from machine import Pin
from credentials import CREDENTIALS

class Etuve:
    params = {
        'temperature_offset' : 0,
        }
    params_json = "params.json"
    
    def __init__(self, 
                 ds_pin:int=None,
                 ):
        self.ds = DS18b20(ds_pin) if ds_pin else None
        self.load_params()
    
    def set_iot(self, iot:FmPyIotWeb):
        self.iot = iot
        self.iot.set_param('etuve', default=self.params, on_change=self.load_params)
        self.iot.add_topic(Topic("./temperature", read=self.get_temperature, send_period=30))

    async def get_temperature(self, **kwargs):
        if self.ds:
            raw_temp = await self.ds.read_async()
            return raw_temp + float(self.params['temperature_offset']) if raw_temp else 0.0
        else:

            return 0.0
    
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

    
etuve = Etuve(ds_pin=27)

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "OLFA/IMPREGNATION/ETUVE",
    watchdog=100,
    sysinfo_period = 600,
    led_wifi="LED",
    web=True,
    name = "Etuve imprégnation",
    logging_level=logging.INFO,
    )

etuve.set_iot(iot)

iot.run(wait = 5)

