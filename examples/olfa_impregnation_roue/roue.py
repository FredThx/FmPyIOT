import uasyncio as asyncio
import logging, json
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicRoutine
from machine import Pin, Timer


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
            self.out_A.irq(trigger=Pin.IRQ_FALLING, handler=self._increment)
        self.output = Pin(output_pin, Pin.OUT) if output_pin else None
        if self.output:
            self.output.off()
        self.out_B = Pin(out_B_pin, Pin.IN) if out_B_pin else None
        self.resolution = resolution
        self.sub_topic = sub_topic
        self.compteur:int=0
        self.load_params()
        #self.tim_check = Timer()
        #self.tim_check.init(period = 20, mode= Timer.PERIODIC, callback=self.check_longueur_atteinte)
        self.tim_coupe= Timer()
    
    def _increment(self, pin:Pin):
        '''Incrémente le compteur de 1 pour chaque impulsion
        Executé par l'irq sur la pin out_A
        '''
        self.compteur += 1
        if self.compteur >= self.compteur_max:
            distance = self.compteur * self.resolution + self.params['offset']
            self.compteur = 0
            self.do_action(distance)
    
    def do_action(self, distance:float):
        '''Action à réaliser lorsque la longueur est atteinte
        '''
        #logging.debug(f"Longueur atteinte : {distance} mm")
        if self.output:
            self.output.on()
            self.tim_coupe.init(period = int(self.params['output_temporisation']*1000), mode= Timer.ONE_SHOT, callback=lambda t:self.output.off())
            asyncio.create_task(self._publish_mqtt(distance))

    async def _publish_mqtt(self, distance:float):
        '''Envoi de la valeur sur le topic MQTT
        '''
        if self.iot:
            await self.iot.publish_async(self.sub_topic, distance)

    def set_iot(self, iot:FmPyIotWeb):
        self.iot = iot
        self.iot.set_param('roue', default=self.params, on_change=self.load_params)
        #self.iot.add_topic(TopicRoutine(action=self.check_longueur_atteinte, send_period=0.5, topic="./roue/check_longueur_atteinte"))

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
        self.compteur_max = int((self.params['longueur']+ self.params['offset']) / self.resolution) # max compteur pour la longueur
        