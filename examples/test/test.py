from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import TopicAction, TopicRead, TopicRoutine, TopicIrq, TopicOnChange
from fmpyiot.device import Device
import asyncio
from machine import Pin, ADC
import logging, time
from pico_render import PicoRender


#WIRING : 
# Shunt Pin 9 et 10

class Test(Device):
    '''
    Class representing a device with tests
    This device has :
    - 1 TopicAction to toggle la Pin 0
    - 1 TopicRead to send the voltage of Pin 29 every 20 seconds
    - 1 TopicIrq to send a message on the topic "./PIN_10" when the state of Pin 10 changes
    - 1 TopicRoutine to run a function in loop
    - 1 TopicRoutine to check if the Pin 15 is stuck low, and if
        if it's the case, send a message to toggle the Pin 0
    A utiliser pour tester les fonctionnalités de FmPyIotWeb
    
    '''
    params = {
        'tempo_run_leds': 0.1,
        'param2': 0,
    }
    def __init__(self,
                 name = "Test pour FmPyIOT"):
        '''
        '''
        super().__init__(name)
        self.pico_render = PicoRender("<h4>GPIO Status</h4>")
        self.pin_LED = Pin(0, Pin.OUT)
        self.load_params()
        self.last_time_pin15_high = 0
        self.status = "???"
    
    def on_load_params(self):
        '''Called on load_params and when parameters are changed'''
        logging.info(f"Parameters loaded : {self.params}")

    def set_iot(self, iot:FmPyIotWeb):
        '''
        Crée les topics MQTT 
        '''
        super().set_iot(iot)
        #Topics Action : à la réception d'un message sur le topic, la fonction est appelée : inverser la valeur de la LED
        self.iot.add_topic(TopicAction("./PIN_0", lambda topic, payload: self.pin_LED.value(not self.pin_LED.value())))
        #Topic Read : toutes les 20 secondes, la fonction est appelée et son résultat est envoyé sur le topic "./voltage"
        self.iot.add_topic(TopicRead("./voltage", lambda topic, payload : ADC(Pin(29)).read_u16()/65535*3.3, send_period=20, reverse_topic="./get_voltage"))
        #Une detection de changement d'état sur une Pin
        self.iot.add_topic(TopicIrq("./PIN_1", pin=Pin(1,Pin.IN,Pin.PULL_UP), trigger = Pin.IRQ_RISING, values=("1","0")))
        #Une routine : la fonction run_leds est appelée en boucle dans une tâche asynchrone
        self.leds = [Pin(i,Pin.OUT) for i in range(2,10)]
        self.index_leds = 0
        async def run_leds():
            while True:
                self.leds[self.index_leds].value(0)
                self.index_leds = (self.index_leds+1)%len(self.leds)
                self.leds[self.index_leds].value(1)
                await asyncio.sleep(self.params['tempo_run_leds'])
        self.iot.add_topic(TopicRoutine(run_leds))
        #Au changement d'état de la Pin 10 envoie d'un message sur le topic "./PIN_10" avec la valeur "1" ou "0". Envoie également la valeur à l'initialisation du device (send_on_init=True)
        self.iot.add_topic(TopicIrq("./PIN_10", pin=Pin(10), trigger= Pin.IRQ_FALLING + Pin.IRQ_RISING, on_irq=self.run_leds_11_15))
        self.leds_11_15 = [Pin(i,Pin.OUT) for i in range(11,16)]
        # Une routine
        self.iot.add_topic(TopicRoutine(self.check_pin_15, send_period=2))
    
    def run_leds_11_15(self, topic, payload):
        '''Fonction appelée à la réception d'un message sur le topic ./RUN_LEDS_11_15 (TopicAction)'''
        logging.info(f"Running leds 11 to 15 with payload : {payload}")
        for led in self.leds_11_15:
            led.value(int(payload))
        
    async def check_pin_15(self):
        '''Fonction appelée toutes les secondes (TopicRoutine)
        Qui check si la Pin 15 est à l'état bas, et quand c'est le cas, envoie un message sur le topic "./PIN_0" pour toogler la LED
        '''
        logging.info("Checking pin 15...")
        timeout = time.time() + 2
        while not Pin(15)() and time.time() < timeout:
            await asyncio.sleep(0.1)
        if time.time() >= timeout:
            self.status = "Error : pin 15 is stuck low !"
        else:
            self.status = "OK, all works fine !"
            await self.iot.publish_async("./PIN_0", "toogle_please")

    def render_web(self):
        '''Called every time the device is rendered (after each topic update)
        '''
        html = "<h1>Test Device</h1>"
        html += f"<p>Test device with parameters : {self.params}</p>"
        html += f"<h5>Status : {self.status}</h5>"
        html += f"""<br><H3>Etat du FmPyIot</H3>
            {self.pico_render.render()}    """
        return html