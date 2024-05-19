from logging import DEBUG
from fmpyiot.fmpyiot import FmPyIot
from fmpyiot.topics import Topic
import uasyncio as asyncio
import logging, time
import machine




class FmPyIotSleep(FmPyIot):
    '''
    Un object connecté branché sur pile
        - qui dort entre chaque envoie de données
        è qui ne reçoit rien (sauf peut-être mode spécial)
    '''
    def __init__(self,
                 mqtt_host: str, mqtt_base_topic: str = None,
                 ssid: str = None, password: str = None,
                 autoconnect: bool = False,
                 watchdog: int = 100,
                 logging_level=logging.DEBUG, log_file="fmpyiot.log", log_maxBytes=10000, log_backupCount=3,
                 name = None, description = None,
                 led_wifi: machine.Pin|int|None = None, led_incoming: machine.Pin|int|None = None, incoming_pulse_duration: float = 0.3,
                 keepalive: int = 120,
                 sleep_period=600, #10 minutes
                 run_pin: machine.Pin|int|None = None, #a pin wired to a transitor qui active/desactive les devices
                 ):
        self.sleep_period = sleep_period
        self.run_pin_function = self.led_function(run_pin) # to enable/disable
        self.run_pin_function(False)
        #On commence par une pause!
        logging.info(f'machine.lightsleep for {self.sleep_period} seconds.')
        time.sleep(1)#Pour avoir le temps d'envoyer le logging
        machine.lightsleep(self.sleep_period*1000)
        print(f'Fin de la sieste!.')
        logging.info("Enable devices")
        self.run_pin_function(True)
        #Avant de vraiment bosser
        super().__init__(mqtt_host, mqtt_base_topic, ssid, password, autoconnect, watchdog, None, logging_level, log_file, log_maxBytes, log_backupCount, name, description, led_wifi, led_incoming, incoming_pulse_duration, keepalive)

    def add_topic(self, topic: Topic):
        '''Add a new topic
        - subscribe to reverse topic
        - publish only one time (sleep_mode)
        '''
        topic.sleep_mode = True
        return super().add_topic(topic)

    ########################
    # Main                  #
    #########################

    async def main(self):
        ''' Connect au broker, puis crée l'ensemble des taches asynchrones.
        puis se place en deepsleep
        '''
        is_connect = False
        while not is_connect:
            try:
                await self.client.connect()
                is_connect = True
            except OSError:
                logging.warning('Connection failed.')
                logging.info("Connect restart in 5 secondes ...")
                await asyncio.sleep(5)
        logging.info(f"SYSINFO :  {await self.sysinfo()}")
        sys_tasks = []
        tasks = []
        for task in (self.up, self.down, self.messages, self.garbage_collector_async, self.get_rtc_async, self.hardware_watchdog_async):
            sys_tasks.append(asyncio.create_task(task()))
        for task in self.routines:
            tasks.append(asyncio.create_task(task()))

        #Web interface
        if self.web:
            sys_tasks.append(self.get_web_task())
        
        #Attente de la fin des taches
        for task in tasks:
            await task
        # Pour rebooter et donc repasser en mode sleep.
        time.sleep(3)#Pour que les envoie mqtt se passent bien.
        machine.reset()
    
    MAX_LIGHT_SLEEP = 3600 # seconds => 1 hour

    def deep_sleep(self, sleep_period:int=None):
        '''Mise en deep_sleep 
        sleep_period    :   secondes
        => reboot au reveil
        '''
        sleep_period = sleep_period or self.sleep_period
        logging.info("Disable devices")
        self.run_pin_function(False) # disable devices
        #logging.info("Close WIFI")
        self.wlan.disconnect()
        self.wlan.active(False)
        self.wlan.deinit()
        machine.Pin('WL_GPIO1'.low())
        logging.info(f'machine.lightsleep for {self.sleep_period} seconds.')
        time.sleep(1)#Pour avoir le temps d'envoyer le logging
        while sleep_period>0:
            lightsleep_duration = min(sleep_period, self.MAX_LIGHT_SLEEP)
            sleep_period -= lightsleep_duration
            machine.lightsleep(lightsleep_duration*1000)
        machine.reset()