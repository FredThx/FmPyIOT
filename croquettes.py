from machine import Pin
from hx711 import HX711
from motor_I298 import MotorI298
import json, time

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
             ):
        self.hx = HX711(hx_data, hx_clk)
        self.motor = MotorI298(motor_pinA, motor_pinB, motor_pin_ena)
        self.motor.stop()
        self.load_params()
        print("Croquettes ready.")   

    params = {
            "hx_gain" : 1993,
            "hx_tare" : 118247 / 1993,
            "motor_speed" : 1,
            "timeout" : 30,
            "autoreverse" : 10,
            "autoreverse_duration" : 1,
            "qty_offset" : 5,
            "motor_speed" : 1,
        }

    def load_params(self):
        '''Initialise les paramètres
        '''
        try:
            with open(self.params_json,"r") as json_file:
                self.params.update(json.load(json_file))
        except OSError as e:
            print(e)

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
    
    def distribute(self,
                qty: float,
                timeout:int = None,
                autoreverse:int = None,
                autoreverse_duration:int = None,
                qty_offset:int = None,
                motor_speed:int = None)-> float:
        '''Verse des croquettes
        qty         :   qte a verser en grammes
        timeout     :   timeout en secondes
        autoreverse :   timeout for autoreverse
        autoreverse_duration : autoreverse duration
        qty_offset  :   reduce the target (erreur de jetée)
        '''
        #Paramètres
        timeout = timeout or self.params.get("timeout")
        autoreverse = autoreverse or self.params.get("autoreverse")
        autoreverse_duration = autoreverse_duration or self.params.get("autoreverse_duration")
        qty_offset = qty_offset or self.params.get("qty_offset")
        motor_speed = motor_speed or self.params.get("motor_speed")
        #Distribution
        tare = self.get_weight()
        target = tare + qty - qty_offset #offset : erreur de jetee
        timeout = time.time() + timeout
        print(f"Ditribution de {qty} grammes de croquettes")
        self.motor.run(duty=self.params["motor_speed"])
        while self.get_weight()<target and time.time()<timeout:
            time_autoreverse = time.time() + autoreverse
            while self.get_weight()<target and time.time()<time_autoreverse:
                print(".",end="")
            if self.get_weight()<target and time.time()<timeout + autoreverse_duration:
                print(f"\nPas assez de croquettes : autoreverse {autoreverse_duration} secondes")
                self.motor.run(reverse = True)
                while self.get_weight()<target and time.time()<time_autoreverse + autoreverse_duration:
                    pass
                self.motor.run(reverse = False)
        self.motor.stop()
        #Résultat : renvoie ce qui a été versé
        time.sleep(1)
        print("")
        return self.get_weight() - tare