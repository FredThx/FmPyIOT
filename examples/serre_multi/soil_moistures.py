import logging, time, json
from machine import Pin
import uasyncio as asyncio
from devices.capacitive_soil_moisture_sensor import Hygrometer
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicAction
from fmpyiot.device import Device

class SoilMoistures(Device):
    """
    Class representing a group of soil moisture sensors
    """
    
    def __init__(self, soil_moistures:list[Hygrometer], base_topic:str="./HYDROS"):
        '''
        '''
        super().__init__(name="soil_moistures", base_topic=base_topic)
        self.soil_moistures = soil_moistures
        for sm in self.soil_moistures:
            sm.parent = self #TODO : a supprimer
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
        super().set_iot(iot)
        for sm in self.soil_moistures:
            iot.add_topic(Topic(f"{self.base_topic}/{sm.name}", read=sm.read, send_period=5))       
            iot.add_topic(TopicAction(f"{self.base_topic}/{sm.name}/calibrate_min", on_incoming=sm.calibre_min)) #TODO : remplacer par lambda
            iot.add_topic(TopicAction(f"{self.base_topic}/{sm.name}/calibrate_max", on_incoming=sm.calibre_max)) #TODO : remplacer par lambda

    def save_calibre(self, sm:Hygrometer, action:str, value:int):
        '''Enregistre la valeur de calibration dans les paramètres
        '''
        self.params[sm.name][f'a_{action}'] = value
        self.save_params()
        logging.info(f"Saved params {sm.name} {action} value: {value}")

    def on_load_params(self):
        '''Applique les paramètres chargés aux capteurs d'humidité de sol
        '''
        for sm in self.soil_moistures:
            if sm.name in self.params:
                sm.a_min = float(self.params[sm.name]['a_min'])
                sm.a_max = float(self.params[sm.name]['a_max'])
            else:
                logging.warning(f"Sensor {sm.name} not found in params, using default values.")