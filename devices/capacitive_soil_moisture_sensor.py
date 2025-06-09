from machine import I2C, Pin
import logging

# TODO : read : renvoyer None si le capteur n'est pas branché ou si la lecture échoue

class Hygrometer:
    ''' A capacitive soil moisture sensor Hygrometer with analogique attachement
    '''
    def __init__(self, reader, a_min:int=800, a_max=400, name:str="Hydrometer") -> None:
        self.reader = reader
        self.a_min = a_min
        self.a_max = a_max
        self.name = name
        self.parent = None  # Reference to the parent SoilMoistures object, if any
        
    def __repr__(self):
        return f"{self.name} : {self.read():.2f}% (min={self.a_min}, max={self.a_max})"

    def read(self)->float:
        '''Read the value of the sensor as a percentage
        The value is between 0 and 100, where 0 is dry and 100 is wet.
        '''
        return max(0.0, min(100.0, (self.reader()-self.a_min) / (self.a_max-self.a_min) * 100.0))

    def calibre_min(self)->int:
        '''Set the minimum value for the sensor.
        This is the value when the soil is dry.
        '''
        self.a_min = self.reader()
        logging.info(f"Calibrated {self.name} min value to {self.a_min}")
        if self.parent:
            self.parent.save_calibre(self, 'min', self.a_min)
    
    def calibre_max(self)->int:
        '''Set the maximum value for the sensor.
        This is the value when the soil is wet.
        '''
        self.a_max = self.reader()
        logging.info(f"Calibrated {self.name} max value to {self.a_max}")
        if self.parent:
            self.parent.save_calibre(self, 'max', self.a_max)
