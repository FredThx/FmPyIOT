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

    def __init__(self, pressure_sensor_bottom:LPS35HW, pressure_sensor_top:BMP280, max_height:float, name:str="reservoir"):
        '''Initialisation
        pressure_sensor_bottom: capteur de pression au fond du réservoir
        pressure_sensor_top: capteur de pression hors du réservoir
        max_height: hauteur maximale du réservoir en cm
        '''
        super().__init__(name)
        self.pressure_sensor_bottom = pressure_sensor_bottom
        self.pressure_sensor_top = pressure_sensor_top
        self.params['max_height'] = max_height
        self.params['pressure_offset'] = 0.0
        self.load_params()
        #Cache des valeurs
        self._top_pressure = None
        self._bottom_pressure = None
        self._contenance = None
        #Reveil des capteurs de pression
        try:
            self.pressure_sensor_bottom.pressure
        except Exception as e:
            pass
        if self.pressure_sensor_top is not None:
            # Le capteur de pression BMP280 est optionnel
            # Il est utilisé pour mesurer la pression hors du réservoir
            self.pressure_sensor_top.pressure
          
    def set_iot(self, iot:FmPyIotWeb):
        super().set_iot(iot)
        iot.add_topic(Topic(f"./contenance", read=self.get_contenance, send_period=5))
        iot.add_topic(TopicAction(f"./calibre", on_incoming=self.calibre))

    def get_contenance(self)->int:
        '''Renvoie la contenance du réservoir en pourcentage
        '''
        try:
            self._top_pressure = self.pressure_sensor_top.pressure
        except Exception as e:
            logging.error(f"Error reading top pressure sensor: {e}")
            self._top_pressure = None
        self._bottom_pressure = self.pressure_sensor_bottom.pressure if self.pressure_sensor_top is not None else None
        if self._top_pressure is None or self._bottom_pressure is None:
            logging.error("Pressure sensors not available")
            self._contenance = None
        else:
            # Calcul de la contenance en fonction des pressions
            hauteur_eau = (self._bottom_pressure - self._top_pressure + self.params['pressure_offset'])  # cm
            self._contenance = hauteur_eau / self.params['max_height'] * 100.0  # Convertir en %
            self._contenance = int(max(0.0, min(100.0, self._contenance)))
        return self._contenance
        
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
    
    def render_web(self)->str:
        '''Renders the web page content
        '''
        level = self.get_contenance() # en pourcentage (0-100)
        no_error = level is not None
        html = f"""<br><H3>Cuve de Fuel Status</H3>
            <p>Contenance de la cuve d'eau : {level} % </p>
            <p>Pression fond cuve : {int(self._bottom_pressure) if self._bottom_pressure is not None else 'N/A'} hPa</p>
            <p>Pression hors cuve : {int(self._top_pressure) if self._top_pressure is not None else 'N/A'} hPa</p>
            <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="100px" height="250px">
                <rect id="fuel" x="10px" y="{230-(level if no_error else 80)}px" width="80px" height="{9 + (level if no_error else 80)}px" fill="{'blue' if no_error else 'red'}" />
                <rect id="tank" x="10px" y="30px" width="80px" height="210px" rx="10px" ry="10px" fill-opacity="0" stroke="black" stroke-width="5px"/>
            </svg>
            """
        return html