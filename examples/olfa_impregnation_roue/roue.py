import uasyncio as asyncio
import logging
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicRoutine
from machine import Pin


class Roue:
    params = {
        'longueur' : 500, # consigne en mm
        'offset' : 0, # erreur lié à la consigne en mm
        'output_temporisation' : 0.5, # durée du signal de sortie en secondes
        }
    params_json = "params.json"
    
    def __init__(self, 
                 out_A_pin:int=None,
                 output_pin:int=None, #Sortie pour pilotage relais coupe
                 out_B_pin:int=None, #Non utilisé pour le moment ( pour sens de rotation)
                 resolution:float=1, # resolution in mm / impulsion
                 sub_topic:str="./distance", # topic pour la publication MQTT
                 ):
        self.out_A = Pin(out_A_pin, Pin.IN) if out_A_pin else None
        if self.out_A:
            self.out_A.irq(trigger=Pin.IRQ_RISING, handler=self._increment)
        self.output = Pin(output_pin, Pin.OUT) if output_pin else None
        self.out_B = Pin(out_B_pin, Pin.IN) if out_B_pin else None
        self.resolution = resolution
        self.sub_topic = sub_topic
        self.compteur:int=0
        self.load_params()
    
    def _increment(self):
        '''Incrémente le compteur de 1 pour chaque impulsion
        Executé par l'irq sur la pin out_A
        '''
        self.compteur += 1
    
    def get_distance(self)->float:
        '''Retourne la distance parcourue en mm
        '''
        return self.compteur * self.resolution + self.params['offset']

    async def check_longueur_atteinte(self)->bool:
        '''Retourne True si la longueur est atteinte
        '''
        distance = self.get_distance()
        if distance >= self.params['longueur']: 
            self.compteur = 0
            await self.do_action(distance)
            return True
        return False

    async def do_action(self, distance:float):
        '''Action à réaliser lorsque la longueur est atteinte
        '''
        print(f"Longueur atteinte : {distance} mm")
        if self.output:
            self.output.on()
            asyncio.create_task(lambda : self._publish_mqtt(distance))
            await asyncio.sleep(self.params['output_temporisation'])
            self.output.off()

    async def _publish_mqtt(self, distance:float):
        '''Envoi de la valeur sur le topic MQTT
        '''
        if self.iot:
            await self.iot.publish(self.sub_topic, distance)

    def set_iot(self, iot:FmPyIotWeb):
        self.iot = iot
        self.iot.set_param('roue', default=self.params, on_change=self.load_params)
        self.iot.add_topic(TopicRoutine(action=self.check_longueur_atteinte, send_period=0.5, topic=f"./measure{i}"))

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
