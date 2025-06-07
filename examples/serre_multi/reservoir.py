import logging
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicAction
from fmpyiot.device import Device
from devices.bmp280 import BMP280
from devices.lps35hw import LPS35HW

class Reservoir(Device):
    """
    Un reservoir dont on peut lire la quantité d'eau
    via deux capteurs de pression
    - un au fond du réservoir
    - un hors du réservoir
    """

    def __init__(self, pressure_sensor_bottom:LPS35HW, pressure_sensor_top:BMP280, max_height:float, name:str="reservoir", base_topic:str="./reservoir"):
        '''Initialisation
        pressure_sensor_bottom: capteur de pression au fond du réservoir
        pressure_sensor_top: capteur de pression hors du réservoir
        max_height: hauteur maximale du réservoir en cm
        '''
        super().__init__(name, base_topic=base_topic)
        self.pressure_sensor_bottom = pressure_sensor_bottom
        self.pressure_sensor_top = pressure_sensor_top
        self.params['max_height'] = max_height
        self.params['pressure_offset'] = 0.0
        self.load_params()
        #Reveil des capteurs de pression
        self.pressure_sensor_bottom.pressure
        self.pressure_sensor_top.pressure
          
    def set_iot(self, iot:FmPyIotWeb):
        super().set_iot(iot)
        iot.add_topic(Topic(f"{self.base_topic}/contenance", read=self.get_contenance, send_period=5))
        iot.add_topic(TopicAction(f"{self.base_topic}/calibre", on_incoming=self.calibre))

    def get_contenance(self)->int:
        '''Renvoie la contenance du réservoir en pourcentage
        '''
        top_pressure = self.pressure_sensor_top.pressure
        bottom_pressure = self.pressure_sensor_bottom.pressure
        if top_pressure is None or bottom_pressure is None:
            logging.error("Pressure sensors not available")
            return None
        # Calcul de la contenance en fonction des pressions
        hauteur_eau = (bottom_pressure - top_pressure + self.params['pressure_offset'])  # cm
        contenance = hauteur_eau / self.params['max_height'] * 100.0  # Convertir en %
        return int(max(0.0, min(100.0, contenance)))
        

    def calibre(self):
        '''Calibre les deux capteurs de pression'''
        top_pressure = self.pressure_sensor_top.pressure
        bottom_pressure = self.pressure_sensor_bottom.pressure
        if top_pressure is None or bottom_pressure is None:
            logging.error("Pressure sensors not available")
            return None
        self.params['pressure_offset'] = top_pressure - bottom_pressure
        self.save_params()
        logging.info(f"Reservoir calibrated with pressure offset: {self.params['pressure_offset']} hPa")

    def on_load_params(self):
        '''Callback when the params are loaded'''
        pass
    