import logging, time
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicRoutine, TopicRead
from fmpyiot.device import Device
from machine import Pin, I2C
from dht import DHT22
from devices.tsl2561 import TSL2561

class Meteo(Device):
    '''
    Un capteur d'humidité + luminosité + température
    '''
    params = {
    }

    def __init__(self, dht_pin:int, i2c:I2C, tls2561_address=0x39, name:str="Méteo Serre"):
        '''
        dht_pin : digital input Pin for DHT22
        i2c : I2C bus for TSL2561
        tls2561_address : I2C address for TSL2561
        '''
        super().__init__(name)
        self.dht = DHT22(Pin(dht_pin))
        self.tls2561 = None
        self.i2c = i2c
        self.tls2561_address = tls2561_address
        self.load_params()
        self._luminosite = 0.0
    
    def on_load_params(self):
        '''Called on load_params and when parameters are changed'''
        pass

    def set_iot(self, iot:FmPyIotWeb):
        '''Crée les topics MQTT pour les capteurs météo
        '''
        super().set_iot(iot)
        iot.add_topic(Topic("./temperature", read=lambda topic, payload : self.dht.temperature(), send_period=30))
        iot.add_topic(Topic("./humidity", read = lambda topic, payload : self.dht.humidity(), send_period=30))
        iot.add_topic(TopicRoutine(self.dht.measure, send_period=10))
        iot.add_topic(TopicRead("./LUMINOSITE", read=self.read_luminosite, send_period=10))

    def read_luminosite(self)->float:
        if self.tls2561 is None:
            try:
                self.tls2561 = TSL2561(self.i2c, address=self.tls2561_address)
            except OSError:
                print("TSL2561 not found")
        if self.tls2561:
            try:
                self._luminosite = self.tls2561.read(autogain=True)
            except OSError:
                logging.error("Error reading TLS2561:")
                self.tls2561 = None
                self._luminosite = 0.0
            except ValueError as e:
                logging.error(f"ValueError reading TLS2561: {e}")
                if "sensor saturated" in str(e):
                    self._luminosite = 2500.0
        return self._luminosite       


    def render_web(self)->str:
        '''Renders the web page content
        '''
        heure = '%s-%s-%s %s:%s:%s'%(time.localtime()[:6])
        html = f"""<br><H3>Station méteo de la serre</H3>
            <p>Current Time: {heure}</p>
            <p>Température : {self.dht.temperature():.1f}°C</p>
            <p>Humidité : {self.dht.humidity():.1f}%</p>
            <p>Luminosité : {self.read_luminosite():.1f} lux</p>
            """
        return html
