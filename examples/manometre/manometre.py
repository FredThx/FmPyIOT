from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicRoutine, TopicIrq
from fmpyiot.device import Device
from machine import Pin, SPI
from fonts.font_56 import font_56
import uasyncio as asyncio

class Manometre(Device):
    '''
    Class representing a Manomètre avec capteur de pression et affichage OLED
    '''
    params = {
        'pression_mini': 3.0,
    }
    def __init__(self,display, key0, mano, name:str="TEST FmPyIot"):
        '''
        display : SH1107 display object
        key0 : Pin object for button
        mano : ManoAnalog object for pressure sensor
        '''
        super().__init__(name)
        self.display = display
        self.key0 = key0
        self.mano = mano
        self.trys = 1
        self.power_display_runners = 0
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
        # Topic pour envoie de la pression via MQTT
        iot.add_topic(Topic("./PRESSION", read=self.mano.read, send_period=20))
        # Routine pour mise à jour de l'ecran
        iot.add_topic(TopicRoutine(self.show_pressure, send_period=1))
        # Routine pour on_off de l'ecran selon bouton key0
        iot.add_topic(TopicIrq("./KEY0", pin=self.key0, trigger = Pin.IRQ_RISING, action=self.power_display))
        iot.add_routine(TopicRoutine(self.power_display))
        self.display_connect()

    def on_pressed(self):
        '''Toggle the output pin
        '''
        self.output_pin(not self.output_pin())        

    def render_web(self)->str:
        '''Renders the web page content
        '''
        pression= self.mano.read()
        html = f"""<br><H3>{self.name}</H3>
            {self.pression} bars.
            <H2>{self.get_icone_pression(pression)}</H2>"""
        return html
    
    def get_icone_pression(self, pression:float)->str:
        '''Retourne une icone selon la pression
        '''
        if pression < self.params['pression_mini']:
            return "🙁"
        else:
            return "😀"

    def display_connect(self):
        self.display.fill(0)
        self.display.text("Demarrage ...",0,5,1)
        self.display.text("Connection a ",5,20,1)
        self.display.text(self.iot.client.server,15,35,1)
        self.display.text(f"Tentative {self.trys}", 0, 55, 1)
        self.trys += 1
        self.display.show()

    def show_pressure(self):
        pression= self.mano.read()
        self.display.fill(1)
        font_56.text(self.display, self.get_icone_pression(pression),0,0)
        self.display.show()
        if pression < 3:
            self.display.poweron()
        elif self.power_display_runners ==0:
            self.display.poweroff()

    async def power_display(self):
        self.display.poweron()
        self.power_display_runners += 1
        await asyncio.sleep(10)
        self.power_display_runners -= 1
        if self.power_display_runners<1:
            self.display.poweroff()
