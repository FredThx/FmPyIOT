import logging, time, json
from machine import Pin
import uasyncio as asyncio
from devices.capacitive_soil_moisture_sensor import Hygrometer
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicAction

class SoilMoistures(object):
    """
    Class representing a group of soil moisture sensors
    """
    params = {
        }
    params_json = "params.json"

    def __init__(self, soil_moistures:list[Hygrometer]):
        '''
        '''
        self.soil_moistures = soil_moistures
        for sm in self.soil_moistures:
            sm.parent = self
            self.params[sm.name] = {
                'a_min': sm.a_min,
                'a_max': sm.a_max,
            }
        self.load_params()
    
    def __iter__(self):
        '''Iterate over the soil moisture sensors'''
        for sm in self.soil_moistures:
            yield sm
    
    def __getitem__(self, key):
        '''Get a soil moisture sensor by name'''
        return self.soil_moistures[key]
          
    def set_iot(self, iot:FmPyIotWeb):
        self.iot = iot
        for sm in self.soil_moistures:
            iot.add_topic(Topic(f"./{sm.name}", read=sm.read, send_period=5))       
            iot.add_topic(TopicAction(f"./{sm.name}/calibrate_min", on_incoming=sm.calibre_min))
            iot.add_topic(TopicAction(f"./{sm.name}/calibrate_max", on_incoming=sm.calibre_max))
        self.iot.set_param('soil_moistures', default=self.params, on_change=self.load_params)

    def save_calibre(self, sm:Hygrometer, action:str, value:int):
        '''Enregistre la valeur de calibration dans les paramètres
        '''
        self.params[sm.name][f'a_{action}'] = value
        self.iot.set_param('soil_moistures', payload=self.params)
        logging.info(f"Saved params {sm.name} {action} value: {value}")

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
        for sm in self.soil_moistures:
            if sm.name in self.params:
                sm.a_min = float(self.params[sm.name]['a_min'])
                sm.a_max = float(self.params[sm.name]['a_max'])
            else:
                logging.warning(f"Sensor {sm.name} not found in params, using default values.")