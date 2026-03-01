from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import TopicAction, TopicRead, TopicRoutine, TopicIrq, TopicOnChange
from fmpyiot.device import Device
import asyncio
from machine import Pin, ADC
import logging, time

class OnChange(Device):
    '''
    Class representing a device with ADC inpuit
    '''
    params = {
    }
    def __init__(self,
                 pin_adc:int,
                 name = "OnChange TEST"):
        '''
        pin_adc : int
        '''
        super().__init__(name)
        self.adc = ADC(Pin(pin_adc))
        self.load_params()
    
    def on_load_params(self):
        '''Called on load_params and when parameters are changed'''
        pass

    def set_iot(self, iot:FmPyIotWeb):
        '''
        Crée les topics MQTT 
        '''
        super().set_iot(iot)
        iot.add_topic(TopicOnChange("./adc", read=self.read_adc, variation =5000, period=0.1, on_change=self.on_change))
        iot.add_topic(TopicAction("./adc", on_incoming=self.on_incoming_adc))

    def read_adc(self, topic, payload):
        '''Read the ADC value and return it
        '''
        val = self.adc.read_u16()
        logging.debug(f"ADC value : {val}")
        return val
    
    def on_incoming_adc(self, topic, payload):
        '''Called when a message is received on the topic ./adc
        '''
        logging.info(f"Message received on topic {topic} with payload {payload}")

    def on_change(self, topic, payload):
        '''Called when the value of the topic ./adc is changed (with a variation of 10000)
        '''
        logging.info(f"Value changed on topic {topic} with payload {payload}")
