import logging, time, json
from machine import Pin
import uasyncio as asyncio
from devices.capacitive_soil_moisture_sensor import Hygrometer
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicAction

class Device(object):
    """
    Une classe abstraite Device qui donne un ménanisme de connexion à FmPyIot
    et de gestion des paramètres.
    """

    def __init__(self, name:str="device", base_topic:str="./device", param_json:str="params.json"):
        '''
        Initialise le device avec un nom
        '''
        self.params = {}
        self.params_json = param_json
        self.name = name
        self.iot = None
        self.base_topic = base_topic
        #self.load_params()

    def set_iot(self, iot:FmPyIotWeb):
        '''Must be implemented by the subclass to set the iot instance
        This method is called to set the iot instance and add the topics
        '''
        self.iot = iot
        self.iot.set_param(self.name, default=self.params, on_change=self.load_params)

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
        self.on_load_params()
    
    def save_params(self):
        '''Sauvegarde les paramètres
        dans un fichier json et dans l'instance iot
        '''
        self.iot.set_param(self.name, payload=self.params)

    def on_load_params(self):
        '''Called when the params are loaded
        This method can be overridden by the subclass to do something when the params are loaded
        '''
        pass