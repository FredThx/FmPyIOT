
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import TopicAction
import logging
from devices.servo import Servo
from devices.bargraph import BarGraph, BarGraphPWM
import json


class AfficheurWC(object):
    '''
    Class representing a WC status display with a servo and a bargraph.
    '''
    params = {
        "angle_libre": 80,
        "angle_occupe": 170,
        "servo_speed": 0.5,
        "facteur_attenuation": 2.0
    }
    params_json = "params.json"

    def __init__(self, servo: Servo, bargraph: BarGraph):
        '''
         servo: Servo object to control the WC door indicator
         bargraph: BarGraph object to display the status
        '''
        self.servo = servo
        self.bargraph = bargraph
        self.state = {
            "etat": None,
            "niveau": None
        }
        self.load_params()
    
    async def set_etat(self, payload):
        if payload.upper() == 'LIBRE':
            await self.servo.move_async(self.params.get("angle_libre",80),speed = self.params.get("servo_speed",0.5))
            self.state["etat"] = "LIBRE"
            logging.info("WC libre")
        else:
            await self.servo.move_async(self.params.get("angle_occupe",170),speed = self.params.get("servo_speed",0.5))
            self.state["etat"] = "OCCUPE"
            logging.info("WC occupé")

    async def set_bargraphe(self, topic:str, payload):
        niveau = int(payload)
        self.bargraph.set_level(niveau, facteur=self.params.get("facteur_attenuation",2.0))
        self.state["niveau"] = niveau
        logging.info(f"Bargraph level set to {niveau}")

    def set_iot(self, iot:FmPyIotWeb):
        self.iot = iot
        iot.add_topic(TopicAction("./ETAT", lambda topic, payload: self.set_etat(payload)))
        iot.add_topic(TopicAction("./BARGRAPH", self.set_bargraphe))
        iot.set_param("afficheur", default=self.params, on_change=self.load_params)
    
    def render_web(self)->str:
        html_content = "<h3>Afficheur WC</h3>"
        html_content += f"<p>État actuel: {self.state['etat']}</p>"
        html_content += f"<p>Niveau du bargraph (qualité de l'air): {self.state['niveau']}</p>"
        return html_content

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


