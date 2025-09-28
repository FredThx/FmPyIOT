
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import TopicAction
import logging
from devices.servo import Servo
from devices.bargraph import BarGraph, BarGraphPWM
import json
from credentials import CREDENTIALS

time.sleep(5)

assert len([])==0, "Error with len!"


class AfficheurWC:
    def __init__(self, servo: Servo, bargraph: BarGraph):
        self.servo = servo
        self.bargraph = bargraph
        self.load_params()
    
    async def set_etat(self, payload):
        if payload == 'libre':
            await self.servo.move_async(self.params.get("angle_libre",80),speed = self.params.get("servo_speed"))
            logging.info("WC libre")
        else:
            await self.servo.move_async(self.params.get("angle_occupe",170),speed = self.params.get("servo_speed"))
            logging.info("WC occupé")

    params = {
        "angle_libre": 80,
        "angle_occupe": 170,
        "servo_speed": 0.5,
    }
    params_json = "params.json"

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

afficheur_wc = AfficheurWC(
    servo=Servo(28),
    bargraph=BarGraphPWM([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
)

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/WC/PORTE",
    watchdog=None,
    sysinfo_period = 600,
    led_wifi='LED',
    web=True,
    name = "AFFICHEUR WC",
    logging_level=logging.DEBUG,
    )


iot.add_topic(TopicAction("./ETAT", lambda topic, payload: afficheur_wc.set_etat(payload)))
iot.add_topic(TopicAction("./BARGRAPH", lambda topic, payload: afficheur_wc.bargraph.set_level(int(payload))))
iot.set_param("afficheur", default=afficheur_wc.params, on_change=afficheur_wc.load_params)


iot.run()