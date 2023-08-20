import logging
from fmpyiot.fmpyiot import FmPyIot



class FLogIotHandler(logging.Handler):
    ''' A handler class witch write logging to a MQTT broker via a FmPyIot object
    '''
    def __init__(self, iot:FmPyIot, mqtt_topic:str = "./LOG", echo:bool=True):
        '''
        iot     :   the iot object
        echo    :   if True, print also log to stdout
        '''
        logging.Handler.__init__(self)
        self.iot = iot
        self.mqtt_topic = mqtt_topic
        self.echo = echo
    
    def emit(self, record):
        self.iot.publish(self.mqtt_topic, record)
        if self.echo:
            print(record)


class FLogIot:
    '''
    '''
    def __init__(self, iot:FmPyIot, console_level = 0, mqtt_level = 0, mqtt_topic:str = "./LOG"):
        self.logger = logging.getLogger()
        #Console handler
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(console_level)
        self.logger.addHandler(self.console_handler)
        #Mqtt handler
        self.mqtt_handler = FLogIotHandler(iot, mqtt_topic)
        self.mqtt_handler.setLevel(mqtt_level)
        self.logger.addHandler(self.mqtt_handler)

