import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicIrq
from fmpyiot.device import Device
from machine import Pin
from pico_render import PicoRender

class Test(Device):
    '''
    Class representing a Test object: 
    '''
    params = {
        "output_pin": 10,
    }

    def __init__(self, input_pin:int, output_pin:int=None, name:str="TEST FmPyIot"):
        '''
        input_pin : digital input Pin
        Output_pin : digital output Pin
        '''
        super().__init__(name)
        self.input_pin = Pin(input_pin, Pin.IN, Pin.PULL_UP)
        if output_pin is not None:
            self.params["output_pin"] = output_pin
        self.pico_render = PicoRender("<h4>GPIO Status</h4>")
        self.load_params()
    
    def on_load_params(self):
        '''Called on load_params and when parameters are changed'''
        self.output_pin = Pin(self.params["output_pin"], Pin.OUT)

    def set_iot(self, iot:FmPyIotWeb):
        '''Crée les topics MQTT pour gérer les GPIO
        1 topic IRQ pour l'input_pin
        1 topic de lecture pour l'output_pin qui est envoyé toutes les secondes
        1 topic action pour simuler une pression sur le bouton via MQTT
        '''
        super().set_iot(iot)
        iot.add_topic(TopicIrq(f"./INPUT", pin=self.input_pin, trigger=Pin.IRQ_FALLING, values=("PRESSED","RELEASED"), on_irq=self.on_pressed,tempo_after_falling=1))
        iot.add_topic(Topic(f"./OUTPUT", read=lambda:self.output_pin(), send_period=1))
        iot.add_topic(Topic(f"./PRESS", action=self.on_pressed))

    def on_pressed(self):
        '''Toggle the output pin
        '''
        self.output_pin(not self.output_pin())        

    def render_web(self)->str:
        '''Renders the web page content
        '''
        heure = '%s-%s-%s %s:%s:%s'%(time.localtime()[:6])
        html = f"""<br><H3>Etat du FmPyIot</H3>
            <p>Current Time: {heure}</p>
            {self.pico_render.render()}    """
        return html