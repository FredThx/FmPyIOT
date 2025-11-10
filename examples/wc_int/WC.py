
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic
from fmpyiot.device import Device
from machine import Pin, ADC

class WC(Device):
    '''
    Class representing a sensor in WC : 
       - a LDR to detect presence
       - a MQ-5 gas sensor to detect bad air quality
    '''
    params = {}

    def __init__(self, gaz_sensor:Pin, ldr:Pin, name:str="WC"):
        '''
         gaz_sensor : ADC Pin connected to MQ-5 gas sensor
         ldr : ADC Pin connected to LDR sensor
        '''
        super().__init__(name)
        self.gaz_sensor = ADC(gaz_sensor)
        self.ldr = ADC(ldr)
        self.load_params()
    
    def set_iot(self, iot:FmPyIotWeb):
        super().set_iot(iot)
        iot.add_topic(Topic(f"./LUM", read=lambda:100*self.ldr.read_u16()/65535, send_period=60))
        iot.add_topic(Topic(f"./MQ-5", read=lambda:100*self.gaz_sensor.read_u16()/65535, send_period=60))
