import logging, time, json
from machine import Pin
import uasyncio as asyncio
from devices.motor_I298 import MotorI298
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicAction
from fmpyiot.device import Device

class Vanne(Device):
    """
    Class representing a valve in a hydraulic system.
    """
    _params = {
        'timeout' : 3000, #Timeout in ms to wait for the valve to open/close
        'delay' : 5, # Delay in ms between each asyncio check
        'delay_plus' : 100, # Additional delay in ms after the valve is opened/closed
        }

    def __init__(self, motor:MotorI298, pin_open:Pin=None, pin_close:Pin=None, timeout:int=None, delay:int=None, delay_plus:int=None, base_topic:str="./vanne"): 
        '''motor: StepperMotor
            pin_open: Pin to check if the valve is open (ie a hall effet sensor)
            pin_close: Pin to check if the valve is closed (ie a hall effet sensor)
        '''
        super().__init__(name="vanne", base_topic=base_topic)
        self.motor = motor
        self.pin_open = pin_open
        if self.pin_open:
            self.pin_open.init(mode=Pin.IN)
        self.pin_close = pin_close
        if self.pin_close:
            self.pin_close.init(mode=Pin.IN)
        self.params["timeout"] = timeout if timeout else self._params["timeout"]
        self.params["delay"] = delay if delay else self._params["delay"]
        self.params["delay_plus"] = delay_plus if delay_plus else self._params["delay_plus"]
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
            await asyncio.sleep_ms(self.params.get('delay_plus',0))  # Give some time to the motor to stop
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
        super().set_iot(iot)
        iot.add_topic(TopicAction(f"{self.base_topic}/open", on_incoming=self.open))
        iot.add_topic(TopicAction(f"{self.base_topic}/close", on_incoming=self.close))
        iot.add_topic(Topic(f"{self.base_topic}/status", read=self.get_status, send_period=5))

    def render_web(self)->str:
        '''Renders the web page content
        '''
        html = f"""<br><H3>Vanne</H3>
            <p>Status : {self.get_status()}</p>
            <p>Pour ouvrir : aller sur {self.base_topic}/open</p>
            <p>Pour fermer : aller sur {self.base_topic}/close</p>
            """
        return html