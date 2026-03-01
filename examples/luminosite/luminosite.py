from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import TopicAction, TopicRead, TopicRoutine
from fmpyiot.device import Device
import asyncio
from devices.tsl2561 import TSL2561
import logging, time

class Luminosite(Device):
    '''
    Class representing a luminosity sensor : the TSL2561
    '''
    params = {
    }
    def __init__(self,
                 i2c,
                 name = "Luminosité semis"):
        '''
        i2c : I2C object
        '''
        super().__init__(name)
        self.i2c = i2c
        try:
            self.sensor = TSL2561(i2c, address=0x39)
        except OSError:
            self.sensor = None
            logging.error("TSL2561 not found")
        self.load_params()
        self._luminosite = None
    
    def on_load_params(self):
        '''Called on load_params and when parameters are changed'''
        pass

    def set_iot(self, iot:FmPyIotWeb):
        '''
        Crée les topics MQTT 
        '''
        super().set_iot(iot)
        iot.add_topic(TopicRead("./LUMINOSITE", read=self.read_sensor, send_period=10))

    def read_sensor(self):
        '''
        Reads the luminosity sensor value
        If sensor is not found, tries to initialize it again at each read
        '''
        if self.sensor is None:
            try:
                self.sensor = TSL2561(self.i2c, address=0x39)
            except OSError:
                logging.error("TSL2561 not found")
        if self.sensor:
            try:
                self._luminosite = self.sensor.read()
            except OSError:
                logging.error("Error reading sensor:")
                self.sensor = None
                self._luminosite = None
        return self._luminosite

    def render_web(self)->str:
        '''Renders the web page content
        '''
        heure = '%s-%s-%s %s:%s:%s'%(time.localtime()[:6])
        html = f"""<br><H3>Luminosité pour les semis</H3>
            <p>Current Time: {heure}</p>
            <p>la luminosité est de {self._luminosite:.1f if self._luminosite is not None else "???"} lux</p>
            """
        return html


