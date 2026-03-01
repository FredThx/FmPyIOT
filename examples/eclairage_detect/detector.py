from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import TopicIrq
from fmpyiot.device import Device
import asyncio
from machine import Pin
import logging, time

class Detector(Device):
    '''
    Class representing une detection par Micro Ondes
    Module : RCWL-0516
    '''
    params = {
    }
    def __init__(self,
                 pin_detector:int=7,
                 output_topic:str=None,
                 name = "Detector"):
        '''
        pin_detector2 : int
        '''
        super().__init__(name)
        self.pin = Pin(pin_detector, Pin.IN, pull=None)
        self.output_topic = output_topic
        self.load_params()
    
    def on_load_params(self):
        '''Called on load_params and when parameters are changed'''
        pass

    def set_iot(self, iot:FmPyIotWeb):
        '''
        Crée les topics MQTT 
        '''
        super().set_iot(iot)
        iot.add_topic(TopicIrq("./detect", pin=self.pin, trigger = Pin.IRQ_RISING, on_irq=self.on_detect))

    async def on_detect(self, *args, **kwargs):
        ''' Envoie d'un message au minuteur de l'éclairage
        '''
        await self.iot.publish_async(self.output_topic,'push')

    def render_web(self)->str:
        '''Renders the web page content
        '''
        heure = '%s-%s-%s %s:%s:%s'%(time.localtime()[:6])
        html = f"""<br><H3>Relais de l'éclairage du couloir du haut</H3>
            <p>Current Time: {heure}</p>
            <p>Detection : {self.pin.value()}</p>
            """
        return html


