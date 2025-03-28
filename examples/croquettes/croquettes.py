from machine import Pin
from devices.hx711 import HX711
from devices.motor_I298 import MotorI298
import json, time, math
import uasyncio as asyncio
import logging


class Croquettes:
    '''Un distributeur de croquette
    avec :
        -   moteur et vis sans fin
        -   un capteur de force via hx711
        -   un raspberry pi pico W
        -   mqtt via wifi/tcp
    '''
    params_json = "params.json"

    def __init__(self,
             hx_clk : Pin,
             hx_data : Pin,
             motor_pinA : Pin,
             motor_pinB : Pin,
             motor_pin_ena : Pin = None,
             vibreur_pinA :Pin = None,
             vibreur_pinB :Pin = None,
             vibreur_ena : Pin = None
             ):
        self.hx = HX711(hx_data, hx_clk)
        self.motor = MotorI298(motor_pinA, motor_pinB, motor_pin_ena)
        self.motor.stop()
        self.vibreur = MotorI298(vibreur_pinA, vibreur_pinB, vibreur_ena)
        self.load_params()
        logging.info("Croquettes ready.")   

    params = {
            "hx_gain" : 1993,
            "hx_tare" : 118247 / 1993,
            "motor_speed" : 0.3, # vitesse initiale du moteur [0-1]
            "timeout" : 30, # seconds
            "autoreverse" : 200, #ms
            "autoreverse_duration" : 100, #ms
            "qty_offset" : 0, # E
            "duration_objectif" : 5000, #ms Temps objectif pour la distribution d'une dose
            "booster" : 0.01
        }

    def load_params(self, params:dict=None):
        '''Initialise les paramètres
            - a partir d'un fichier json
            - ou d'un dict en entrée 
        '''
        if params:
            self.params.update(params)
        else:
            try:
                with open(self.params_json,"r") as json_file:
                    self.params.update(json.load(json_file))
            except OSError as e:
                logging.error(str(e))
        print(f"Params loaded. New params : {self.params}")

    def set_params(self, volatil: bool = False, **kwargs):
        '''Met à jour un ou plusieur paramètres
        volatil     :   if True, the params are not stored in json file
        '''
        self.params.update(kwargs)
        if not volatil:
            with open(self.params_json,"w") as json_file:
                json.dump(kwargs, json_file)

    def get_hx_value(self)->int:
        '''return the raw value of the hx711 device
        '''
        return self.hx.read()

    def get_weight(self):
        '''Return the weight in the receiver
        '''
        return self.get_hx_value() / self.params["hx_gain"] - self.params["hx_tare"]
    
    async def distribute_async(self,
                qty: float,
                timeout:int = None,
                autoreverse:int = None,
                autoreverse_duration:int = None,
                qty_offset:float = None,
                motor_speed:float = None,
                duration_objectif = None,
                booster: float = None)-> float:
        '''Verse des croquettes
        qty                 :   qte a verser en grammes
        timeout             :   timeout en secondes
        autoreverse         :   timeout for autoreverse
        autoreverse_duration: autoreverse duration
        qty_offset          :   reduce the target (erreur de jetée en gramme)
        motor_speed         :   initial motor speed
        duration_objectif   :   target duration (ms) to distribute a dose
        booster             :   incremente for booster ex 0.01
        '''
        #Paramètres
        timeout = timeout or self.params.get("timeout")
        autoreverse = autoreverse or self.params.get("autoreverse")
        autoreverse_duration = autoreverse_duration or self.params.get("autoreverse_duration")
        qty_offset = qty_offset or self.params.get("qty_offset")
        motor_speed = motor_speed or self.params.get("motor_speed")
        booster = booster or self.params.get('booster')
        duration_objectif = duration_objectif or self.params.get("duration_objectif") or timeout / 3
        #Distribution
        tare = self.get_weight()
        target = tare + qty - qty_offset #offset : erreur de jetee
        timeout = time.time() + timeout
        logging.info(f"Ditribution de {qty} grammes de croquettes")
        self.motor.stop()
        self.motor.duty=motor_speed
        boost=0
        start0_ms = time.ticks_ms()
        while self.get_weight()<target and time.time()<timeout:
            start_ms = time.ticks_ms()
            duty = min(1,self.motor.duty*math.exp(boost))
            self.motor.run(reverse = False, duty = duty)
            while self.get_weight()<target and time.ticks_diff(time.ticks_ms(), start_ms)<autoreverse*math.exp(boost):
                await asyncio.sleep_ms(5)
            start_ms = time.ticks_ms()
            self.motor.stop()
            self.motor.run(reverse = True)
            while (weight:=self.get_weight())<target and time.ticks_diff(time.ticks_ms(), start_ms)<autoreverse_duration*math.exp(boost):
                await asyncio.sleep_ms(5)
            if weight < qty/duration_objectif*time.ticks_diff(time.ticks_ms(), start0_ms) + tare:
                boost+=booster
            self.motor.stop()
        #Résultat : renvoie ce qui a été versé
        await asyncio.sleep(1)
        logging.info(f"{self.get_weight() - tare} grammes distribués")
        return self.get_weight() - tare

    async def vibre_async(self, duration:float = 10.0, duty:float = 0.7, duration_on:int|float = 1, duration_off:int|float = 1):
        '''Vibre pendant x secondes
        '''
        if self.vibreur:
            logging.info(f"Vibration pendant {duration} secondes, duty = {duty}")
            timeout = time.ticks_add(time.ticks_ms(), int(duration *1000))
            while time.ticks_diff(time.ticks_ms(), timeout) < 0:
                logging.debug("vibreur ON")
                self.vibreur.run(duty = duty)
                await asyncio.sleep(duration_on)
                logging.debug("vibreur OFF")
                self.vibreur.stop()
                await asyncio.sleep(duration_off)
            logging.debug("Vibration terminée")
        else:
            logging.warning("no vibreur!")

    def run_motor(self,value:float):
        '''Run the motor
        value : [-1;1]
        '''
        if value < 0:
            self.motor.run(duty=-value, reverse = True)
        elif value > 0:
            self.motor.run(duty=value, reverse = False)
        else:
            self.motor.stop()