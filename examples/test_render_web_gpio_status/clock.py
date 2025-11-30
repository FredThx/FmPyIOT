import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicIrq
from fmpyiot.device import Device
from machine import Pin
from pico_render import PicoRender

class Clock(Device):
    '''
    Class representing a Test object: une horloge affichant l'heure courante
    '''
    params = {
        "title": "Horloge",
    }

    def __init__(self, name:str="TEST FmPyIot : Clock"):
        '''
        '''
        super().__init__(name)
        self.load_params()

    def render_web(self)->str:
        '''Renders the web page content
        '''
        heure = '%s-%s-%s %s:%s:%s'%(time.localtime()[:6])
        html = f"""
            <h4>{self.params['title']}</h4>
            <div>Current Time: {heure}</div>"""
        return html