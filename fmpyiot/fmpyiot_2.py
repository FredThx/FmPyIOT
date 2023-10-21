from mqtt_as.mqtt_as import MQTTClient, config as mqtt_as_config
import uasyncio as asyncio
import logging
from machine import Pin
from fmpyiot.topics import Topic

logging.basicConfig(level=logging.DEBUG)

class FmPyIot:
    '''Un objet connecté via mqtt (et plus:todo)
    '''
    def __init__(self,
            mqtt_host:str, mqtt_client_name:str = None, mqtt_base_topic:str = None,
            ssid:str = None, password:str = None,
            callback:function = None,
            timeout:int = 60,
            autoconnect:bool = False,
            watchdog:int = 100,
            mqtt_check_period:int = 100, #ms
            debug:bool = True,
            sysinfo_period:int = 600, #s
            country = 'FR',
            async_mode = True,
            mqtt_log = "./LOG",
            log_console_level = logging.DEBUG,
            log_mqtt_level = logging.INFO,
            web = False,
            web_port = 80,
            led_wifi = None,
            led_incoming = None,
            incoming_pulse_duration = 0.3,
            keepalive = 120,
                 ):
        self.outages = 0
        self.led_wifi = self.led_function(led_wifi)
        self.led_incoming = self.led_function(led_incoming)
        self.incoming_pulse_duration = incoming_pulse_duration
        self.mqtt_base_topic = mqtt_base_topic + "/" if mqtt_base_topic[-1]!="/" else ""
        # mqtt_as_config : default mqtt_as config
        mqtt_as_config['server'] = mqtt_host
        mqtt_as_config['ssid']     = ssid
        mqtt_as_config['wifi_pw']  = password
        mqtt_as_config['will'] = (self.get_topic("./BYE"), 'Goodbye cruel world!', False, 0)
        mqtt_as_config['keepalive'] = keepalive
        mqtt_as_config["queue_len"] = 1  # Use event interface with default queue
        MQTTClient.DEBUG = True
        self.client = MQTTClient(mqtt_as_config)
        if autoconnect:
            self.run()
        self.callbacks = {} #{'topic' : callback}
        self.auto_send_topics = []

    #########################
    # DIVERS utilitaires    #
    #########################
    def get_topic(self, topic:str)-> str:
        '''Ajout base_topic quand './' devant
        '''
        if self.mqtt_base_topic and topic[:2]=="./":
            return self.mqtt_base_topic + topic[2:]
        else:
            return topic

    @staticmethod
    def led_function(led: None | int | Pin)-> function:
        '''Renvoie une fonction qui pilote une led
        (intéret : led peut être None ou int ou Pin)
        '''
        if led is None : return lambda _:None
        if type(led)!=Pin:
            led = Pin(led)
        led.init(Pin.OUT,value = 0)
        def func(v:bool):
            led(v)
        return func

    async def pulse(self):
        ''' Pulses incoming LED each time a subscribed msg arrives.
        '''
        self.led_incoming(True)
        await asyncio.sleep(self.incoming_pulse_duration)
        self.led_incoming(False)


    ####################################
    # Utilisation de la lib mqtt_as    #
    ####################################
    async def messages(self):
        ''' Traite tous les messages entrants
        '''
        async for topic, msg, retained in self.client.queue:
            topic = topic.decode()
            payload = msg.decode()
            print(f'Incoming : "{topic}" : "{payload}" Retained: {retained}')
            asyncio.create_task(self.pulse())
            if topic in self.callbacks:
                callback = self.callbacks[topic]
                if callback:
                    try:
                        asyncio.create_task(callback(topic, payload))
                    except TypeError:
                        pass #En fait callback(topic, payload) a déjà été executée ci-dessus
            else:
                logging.warning(f"Unknow topic : {topic}")

    async def down(self,):
        ''' Deamon qui gère la perte de connectivité
        '''
        while True:
            await self.client.down.wait()  # Pause until connectivity changes
            self.client.down.clear()
            self.led_wifi(False)
            self.outages += 1
            logging.warning('WiFi or broker is down.')

    async def up(self):
        ''' Deamon qui gère la connection
        '''
        while True:
            await self.client.up.wait()
            self.client.up.clear()
            self.led_wifi(True)
            logging.info('We are connected to broker.')
            for topic in self.callbacks:
                await self.client.subscribe(topic, 0)
    
    def publish(self, topic:str, payload:str, qos = 0):
        '''Publish on mqtt (sauf si topic = None)
        '''
        if topic is not None:
            logging.info(f'publish {topic} : {payload}')
            asyncio.create_task(self.client.publish(self.get_topic(topic), str(payload), qos = qos))

    #########################
    # Gestion des Topics   #
    #########################

    def subscribe(self, topic:str, callback:function = None):
        '''Subscibe to a mqtt topic 
        callback : function(topic, payload)
        '''
        topic = self.get_topic(topic)
        logging.info(f"Subscribe {topic} : callback={callback}")
        #Ce serait bien de detecter ici si callback est une coroutine (sans l'executer) : ca éviterais de la faire à chaque fois
        self.callbacks[topic]=callback

    def add_topic(self, topic:Topic):
        '''Add a new topic
        - subscribe to reverse topic
        '''
        if topic.reverse_topic():
            self.subscribe(
                topic.reverse_topic(),
                lambda _topic, _payload: self.publish(str(topic),topic.get_payload(_topic, _payload))
                )
        if topic.action:
            self.subscribe(
                str(topic),
                lambda _topic, _payload: self.publish(topic.reverse_topic(),topic.do_action(_topic, _payload))
                )
        if topic.send_period:
            self.auto_send_topics.append(topic)
        # Essentiellement pour IRQ
        topic.attach(self)
    
    def publish_topic(self, topic:Topic):
        '''publish
        '''
        logging.debug(f"publish_topic({topic})")
        self.publish(str(topic),topic.get_payload())

   
    #########################
    # Main                  #
    #########################

    async def main(self):
        try:
            await self.client.connect()
        except OSError:
            logging.warning('Connection failed.')
            return
        for task in (self.up, self.down, self.messages):
            asyncio.create_task(task())
        while True:
            await asyncio.sleep_ms(100)
            for topic in self.auto_send_topics:
                topic.auto_send(self.publish_topic)

    def run(self):
        try:
            asyncio.run(self.main())
        finally:  # Prevent LmacRxBlk:1 errors.
            self.client.close()
            asyncio.new_event_loop()


if __name__=='__main__':
    iot=FmPyIot(
        mqtt_host="***REMOVED***",
        mqtt_base_topic= "test",
        ssid = 'WIFI_THOME2',
        password = "***REMOVED***",
        watchdog=100,
        sysinfo_period = 600,
        led_incoming="LED", #internal
        led_wifi=16
        )
    iot.run()