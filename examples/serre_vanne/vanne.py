import logging, time, json
from machine import Pin
import uasyncio as asyncio
from devices.motor_I298 import MotorI298
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicAction

class Vanne(object):
    """
    Class representing a valve in a hydraulic system.
    """
    params = {
        'timeout' : 1000, #Timeout in ms to wait for the valve to open/close
        'delay' : 5, # Delay in ms between each asyncio check
        }
    params_json = "params.json"

    def __init__(self, motor:MotorI298, pin_open:Pin=None, pin_close:Pin=None, timeout:int=None, delay:int=None):
        '''motor: StepperMotor
            pin_open: Pin to check if the valve is open (ie a hall effet sensor)
            pin_close: Pin to check if the valve is closed (ie a hall effet sensor)
        '''
        self.motor = motor
        self.pin_open = pin_open
        if self.pin_open:
            self.pin_open.init(mode=Pin.IN)
        self.pin_close = pin_close
        if self.pin_close:
            self.pin_close.init(mode=Pin.IN)
        self.params["timeout"] = timeout if timeout else self.params["timeout"]
        self.params["delay"] = delay if delay else self.params["delay"]
        self.load_params()
        

    async def open_close(self, open:bool=True):
        '''Open or close the valve'''
        logging.info(f"{'Opening' if open else 'Close'} the  valve.")
        stop_status = "open" if open else "closed"
        logging.debug(f"Waiting for the valve to be {stop_status}...")
        if self.get_status() != stop_status:
            self.motor.run(reverse=not open)
            timeout = time.ticks_add(time.ticks_ms(), self.params["timeout"])
            logging.debug(f"status = {self.get_status()}")
            while (self.get_status() not in [stop_status, "error"]) and time.ticks_diff(timeout, time.ticks_ms()) > 0:
                await asyncio.sleep_ms(self.params['delay'])
                logging.debug(f"status = {self.get_status()}")
        else:
            logging.info(f"Valve is already {stop_status}.")
        self.motor.stop()

    async def open(self):
        '''Open the valve'''
        await self.open_close(True)
    async def close(self):
        '''Close the valve'''
        await self.open_close(False)    
    
    def get_status(self):
        """
        Get the status of the valve ("open" or "closed" or "unknow" or "error").
        """
        if self.pin_open and self.pin_close:
            if self.pin_open.value() == 0 and self.pin_close.value() == 0:
                return "error"
        if self.pin_open and self.pin_open.value() == 0:
            return "open"
        if self.pin_close and self.pin_close.value() ==0:
            return "closed"
        return "unknown"
    
    def set_iot(self, iot:FmPyIotWeb):
        self.iot = iot
        iot.add_topic(TopicAction("./open", on_incoming=self.open))
        iot.add_topic(TopicAction("./close", on_incoming=self.close))
        iot.add_topic(Topic("./status", read=self.get_status, send_period=5))
        self.iot.set_param('vanne', default=self.params, on_change=self.load_params)

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