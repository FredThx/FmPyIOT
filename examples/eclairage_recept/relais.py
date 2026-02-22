from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import TopicAction, TopicRead, TopicRoutine
from fmpyiot.device import Device
import asyncio
from machine import Pin
import logging, time

class Relais(Device):
    '''
    Class representing two relais used like a push button
    '''
    params = {
        "duration":500 # ms
    }
    def __init__(self,
                 pin_relay1:int=7,
                 pin_relay2:int=6,
                 name = "Relais Eclairage Couloir haut"):
        '''
        pin_relais1&2 : int
        '''
        super().__init__(name)
        self.relay1 = Pin(pin_relay1, Pin.OUT)
        self.relay2 = Pin(pin_relay2, Pin.OUT)
        self.load_params()
    
    def on_load_params(self):
        '''Called on load_params and when parameters are changed'''
        pass

    def set_iot(self, iot:FmPyIotWeb):
        '''
        Crée les topics MQTT 
        '''
        super().set_iot(iot)
        iot.add_topic(TopicAction("./relais1", on_incoming=self.on_incoming1))
        iot.add_topic(TopicAction("./relais2", on_incoming=self.on_incoming2))

    async def on_incoming1(self, topic, payload):
        '''
        A la reception d'un message : on active le relai 1
        '''
        await self.push(self.relay1)

    async def on_incoming2(self, topic, payload):
        '''
        A la reception d'un message : on active le relai 2
        '''
        await self.push(self.relay2)

    async def push(self, relay):
        '''
        Ferme le relai pendant duration ms
        '''
        logging.info(f"{relay} ON")
        relay.on()
        await asyncio.sleep_ms(self.params.get('duration',500))
        logging.info(f"{relay} OFF")
        relay.off()

    def render_web(self)->str:
        '''Renders the web page content
        '''
        heure = '%s-%s-%s %s:%s:%s'%(time.localtime()[:6])
        html = f"""<br><H3>Relais de l'éclairage du couloir du nhaut</H3>
            <p>Current Time: {heure}</p>
            <p>Pour allumer : aller sur topics</p>
            """
        return html


