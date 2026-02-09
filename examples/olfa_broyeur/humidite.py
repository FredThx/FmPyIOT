from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import TopicAction, TopicRead, TopicRoutine
from fmpyiot.device import Device
import dht
from machine import Pin
import logging, time

class Humidity(Device):
    '''
    Class representing a humidityure sensor using a DHT22 sensor. It measures the humidity and temperature.
    '''
    params = {
    }
    def __init__(self,
                 pin_dht:int=16,
                 name = "Humidity"):
        '''
        pin_dht : Pin for DHT22 sensor
        '''
        super().__init__(name)
        self.dht = dht.DHT22(Pin(pin_dht))
        self.load_params()
    
    def on_load_params(self):
        '''Called on load_params and when parameters are changed'''
        pass

    def set_iot(self, iot:FmPyIotWeb):
        '''
        Crée les topics MQTT 
        '''
        super().set_iot(iot)
        #iot.add_routine(TopicRoutine(self.measure, send_period=50, topic = "./measure"))
        iot.add_topic(TopicRead("./humidity", read= self.read_humidity, send_period=60))
        iot.add_topic(TopicRead("./temperature", read= self.dht.temperature, send_period=60))
    
    def read_humidity(self):
        '''Mesure la température et l'humidité. Et renvoie de l'umidité'''
        logging.info("Measuring humidity and temperature")
        self.dht.measure()
        return self.dht.humidity()

    def render_web(self)->str:
        '''Renders the web page content
        '''
        heure = '%s-%s-%s %s:%s:%s'%(time.localtime()[:6])
        html = f"""<br><H3>Humidité du broyage</H3>
            <p>Current Time: {heure}</p>
            <p>Humidité : {self.dht.humidity()} %</p>
            <p>Température : {self.dht.temperature()} °C</p>
            """
        return html


