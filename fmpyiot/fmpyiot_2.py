from mqtt_as.mqtt_as import MQTTClient, config as mqtt_as_config
import uasyncio as asyncio
import logging, os, ubinascii, gc, json, network
from machine import Pin
from fmpyiot.topics import Topic
from fmpyiot.wd import WDT

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
        self.wlan = self.client._sta_if
        if autoconnect:
            self.run()
        self.callbacks = {} #{'topic' : callback}
        self.auto_send_topics = []
        #Watchdog
        self.wd = None
        if watchdog:
            self.init_watchdog(watchdog)
        if sysinfo_period:
            self.init_system_topics(sysinfo_period)
        self.params_loaders = []

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
            logging.info(f'Incoming : "{topic}" : "{payload}" Retained: {retained}')
            asyncio.create_task(self.pulse())
            if topic in self.callbacks:
                callback = self.callbacks[topic]
                if callback:
                    try:
                        asyncio.create_task(callback(topic, payload))
                    except TypeError: #Si la callback n'est pas une coroutine
                        logging.error("OUPS ON NE DEVRAIT PLUS PASSER PAR LA!")
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
            asyncio.create_task(self.client.publish(self.get_topic(topic), json.dumps(payload), qos = qos))

    async def a_publish(self, topic:str, payload:str, qos = 0):
        if topic is not None:
            logging.info(f'a_publish {topic} : {payload}')
            await self.client.publish(self.get_topic(topic), json.dumps(payload), qos = qos)

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
            async def callback(_topic, _payload):
                return await self.a_publish(
                    str(topic),
                    await topic.a_get_payload(_topic, _payload))
            self.subscribe(
                topic.reverse_topic(),
                callback
                )
        if topic.action:
            async def callback(_topic, _payload):
                return self.a_publish(
                    topic.reverse_topic(),
                    await topic.a_do_action(_topic,_payload))
            self.subscribe(
                str(topic),
                callback
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
    
    async def a_publish_topic(self, topic:Topic):
        logging.debug(f"publish_topic({topic})")
        payload = await topic.a_get_payload()
        await self.a_publish(str(topic),payload)


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
        except KeyboardInterrupt:
            pass
        finally:  # Prevent LmacRxBlk:1 errors.
            logging.info("Main routine stopped.")
            self.client.close()
            asyncio.new_event_loop()

    #########################
    # SYSTEM                #
    #########################

    def init_watchdog(self, watchdog_delai:int):
        '''Create a new Topic with watchdog
        watchdog_delai  :   delai (seconds) before restarting device
        '''
        self.wd = WDT(watchdog_delai)
        self.wd.enable()
        self.add_topic(Topic(
                    "./WATCHDOG",
                    send_period=int(watchdog_delai/3),
                    reverse_topic=False,
                    read=lambda topic, payload:"FEED",
                    action=lambda topic, payload: self.wd.feed()
                    ))

    def init_system_topics(self, period:int):
        '''Create system topics
        '''
        self.add_topic(Topic(
                    "./SYSINFO",
                    send_period=period,
                    read=self.sysinfo
                    ))
        self.add_topic(Topic(
                    "./SET_PARAMS",
                    reverse_topic=False,
                    action = self.set_params
        ))
        self.add_topic(Topic(
                    "./_PARAMS",
                    read = self.get_params
        ))

    async def sysinfo(self)->dict:
        '''renvoie les informations system
        '''
        return{
            'uname' : list(os.uname()),
            'ifconfig' : self.wlan.ifconfig(),
            'wifi' : {k:self.wlan.config(k) for k in ['ssid', 'channel', 'txpower']},
            'mac' : ubinascii.hexlify(self.wlan.config('mac'),':').decode(),
            'mem_free' : gc.mem_free(),
            'mem_alloc' : gc.mem_alloc(),
            'statvfs' : os.statvfs('/')
        }

    params_json = "params.json"

    def get_params(self)->dict:
        '''Renvoie le contenu de params_json
        '''
        try:
            with open(self.params_json,"r") as json_file:
                return json.load(json_file)
        except OSError as e:
            print(e)
    
    def set_params(self, topic:bytes, payload:bytes):
        '''Met à jour le fichier params_json en fonction de payload
        '''
        params = self.get_params()
        try:
            params.update(json.loads(payload))
        except Exception as e:
            print(e)
        try:
            with open(self.params_json,"W") as json_file:
                json.dump(params, json_file)
        except OSError as e:
            print(e)
        for loader in self.params_loaders:
            try:
                loader()
            except Exception as e:
                print(f"Error on params_loader {loader} : {e}")
    
    def set_params_loader(self, loader:function):
        self.params_loaders.append(loader)
    
    network_status = {
        network.STAT_IDLE : "Link DOWN", #(0 : CYW43_LINK_DOWN)
        network.STAT_CONNECTING : "Link JOIN or Timeout", #(1 : CYW43_LINK_JOIN)
        2 : "Link NO IP", #(2 : CYW43_LINK_NOIP)
        network.STAT_GOT_IP : "Link UP (sucess)", #(3 : CYW43_LINK_UP)
        network.STAT_CONNECT_FAIL : "Link FAIL", #(-1 : CYW43_LINK_FAIL)
        network.STAT_NO_AP_FOUND : "Link NO NET", #(-2 : CYW43_LINK_NONET)
        network.STAT_WRONG_PASSWORD : "Link BAD AUTH", #(-3 : CYW43_LINK_BADAUTH)
    }
    def str_network_status(self):
        '''renvoie le status de la connection au format string
        '''
        return self.network_status[self.wlan.status()]

    def __repr__(self):
        repr = f"""FmPyIot(version2)({self.mqtt_base_topic})
                WIFI : {self.str_network_status()}
                WD : {self.wd}
                callbacks : \n"""
        for topic in self.callbacks:
            repr += f"\t\t\t{topic}\n"
        return repr
    
    def dm(self):
        '''place de dispositif en mode debug'''
        self.wd.disable()
        print('Watchdog desactivate')


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