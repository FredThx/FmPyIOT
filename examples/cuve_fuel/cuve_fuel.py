from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import TopicAction, TopicRead
from fmpyiot.device import Device
from devices.lidar import TF_Luna
from machine import Pin, I2C
import logging, time

class CuveFuel(Device):
    '''
    Class representing a fuel tank level measurement system using a TF-Luna Lidar.
    It measures the distance to the fuel surface and controls indicator LEDs.
    '''
    params = {
        'lidar_min' : 20,
        'lidar_max' : 800,
        'lidar_freq' : 100
    }
    def __init__(self,
                 pin_scl:int=9, pin_sda:int=8, i2c_freq:int=400_000,
                 lida_freq:int=100,lidar_min:int=20, lidar_max:int=800,
                 pin_led_rouge:int=1, pin_led_vert:int=0,
                 name = "Cuve de Fuel"):
        '''
        pin_scl : I2C SCL pin
        pin_sda : I2C SDA pin
        i2c_freq : I2C frequency
        lida_freq : TF-Luna measurement frequency
        lidar_min : TF-Luna minimum distance (in mm)
        lidar_max : TF-Luna maximum distance (in mm)
        pin_led_rouge : Pin for red LED indicator
        pin_led_vert : Pin for green LED indicator
        '''
        super().__init__(name)
        self.i2c = I2C(0, scl=Pin(pin_scl), sda=Pin(pin_sda), freq = i2c_freq)
        self.lidar = TF_Luna(self.i2c, min=lidar_min, max=lidar_max, freq = lida_freq)
        self.leds = {
            'rouge' : Pin(pin_led_rouge, Pin.OUT),
            'vert' : Pin(pin_led_vert,Pin.OUT)
            }
        self.load_params()
    
    def on_load_params(self):
        '''Called on load_params and when parameters are changed'''
        logging.info(f"cuve_fuel.load_params({self.param})")
        self.lidar = TF_Luna(self.i2c,
                            min=int(self.param['lidar_min']),
                            max=int(self.param['lidar_max']),
                            freq = int(self.param['lidar_freq']))

    def set_iot(self, iot:FmPyIotWeb):
        '''
        Crée les topics MQTT pour gérer la cuve de fuel
        ./distance : topic de lecture (sortant) de la distance mesurée par le Lidar
                    encoyée toutes les 10 secondes
        ./LED : topic action (entrant) pour contrôler les LEDs indicatrices
        '''
        super().set_iot(iot)
        iot.add_topic(TopicRead("./distance", read= self.read_distance, send_period=10))
        iot.add_topic(TopicAction("./LED", action = lambda topic, payload : self.set_leds(payload)))
    
    def read_distance(self, *args, **kwargs):
        '''Lit la distance mesurée par le Lidar'''
        return self.lidar.distance()

    def set_leds(self, payload:str):
        '''Allume ou éteint les LEDs en fonction de la payload reçue
        payload : 'rouge' ou 'vert'
        '''
        logging.info(f"Set led = '{payload}'")
        for key, led in self.leds.items():
            if key == payload:
                led.on()
            else:
                led.off()

    def render_web(self)->str:
        '''Renders the web page content
        '''
        heure = '%s-%s-%s %s:%s:%s'%(time.localtime()[:6])
        html = f"""<br><H3>Cuve de Fuel Status</H3>
            <p>Current Time: {heure}</p>
            <p>Distance mesurée : {self.read_distance()} mm</p>
            <p>LED Rouge : {'ON' if self.leds['rouge']() else 'OFF'}</p>
            <p>LED Vert : {'ON' if self.leds['vert']() else 'OFF'}</p>
            """
        return html


