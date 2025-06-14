import gc
gc.collect()
from mqtt_as.mqtt_as import MQTTClient, config as mqtt_as_config
gc.collect()
import uasyncio as asyncio
import logging, os, ubinascii, gc, json, network, time, re
from logging.handlers import RotatingFileHandler
import machine
gc.collect()
from fmpyiot.topics import Topic, TopicRoutine
gc.collect()
from fmpyiot.wd import WDT
gc.collect()
from fmpyiot.params import FmPyIotParam, FmPyIotParams
gc.collect()


logging.basicConfig(level=logging.DEBUG)

class FmPyIot:
    '''Un objet connecté via mqtt
    '''
    def __init__(self,
            mqtt_host:str, mqtt_base_topic:str = "",
            ssid:str = None, password:str = None,
            autoconnect:bool = False,
            watchdog:int = 100,
            sysinfo_period:int = 600, #s
            logging_level = logging.DEBUG,
            log_file = "fmpyiot.log",
            log_maxBytes = 10_000,
            log_backupCount = 3,
            name = None,
            description = None,
            led_wifi:machine.Pin|int|None = None,
            led_incoming:machine.Pin|int|None = None,
            incoming_pulse_duration:float = 0.3,
            keepalive:int = 120,
            on_fail_connect:callable = None,
            country='FR'
                 ):
        self.name = name or mqtt_base_topic
        self.description = description or "FmPyIot"
        self.params = FmPyIotParams()
        #RTC
        self.rtc = machine.RTC()
        self.rtc_is_updated = False
        self.set_rtc_from_params()
        #Logging level
        self.logger = logging.getLogger()
        self.client = None
        self.set_logging_level(logging_level)
        self.log_file = log_file
        if self.log_file:
            file_handler = RotatingFileHandler(self.log_file, maxBytes=log_maxBytes, backupCount = log_backupCount)
            file_handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s: %(asctime)s : %(message)s"))
            self.logger.addHandler(file_handler)
        logging.info("FmPyIOT start.")
        # Initialisations
        self.routines:list[TopicRoutine] = []
        self.topics:list[Topic]= []
        self.outages = 0
        self.led_wifi = self.led_function(led_wifi)
        self.led_incoming = self.led_function(led_incoming)
        self.incoming_pulse_duration = incoming_pulse_duration
        self.mqtt_base_topic = mqtt_base_topic + ("/" if mqtt_base_topic[-1]!="/" else "")
        # mqtt_as_config : default mqtt_as config
        mqtt_as_config['server'] = mqtt_host
        mqtt_as_config['ssid']     = ssid
        mqtt_as_config['wifi_pw']  = password
        mqtt_as_config['will'] = (self.get_topic("./BYE"), 'Goodbye cruel world!', False, 0)
        mqtt_as_config['keepalive'] = keepalive
        mqtt_as_config["queue_len"] = 1  # Use event interface with default queue
        #MQTTClient.DEBUG = True
        self.client = MQTTClient(mqtt_as_config)
        self.wlan = self.client._sta_if
        #TODO : à tester
        network.country(country)
        try:
            network.hostname(re.sub(r'[^a-zA-Z0-9]', '', self.name)[32])  # Set the hostname for the device
        except:
            pass
        #fin TODO à tester
        self.callbacks = {} #{'topic' : callback}
        self.set_logging_level(logging_level)
        #Watchdog
        self.wd = None
        self.watchdog = watchdog
        #Divers
        if sysinfo_period:
            self.init_system_topics(sysinfo_period)
        self.params.set_loader('rtc',  lambda _ : self.set_rtc_from_params())
        self.web=None
        #Auto run
        if autoconnect:
            self.run()
        self.on_fail_connect = on_fail_connect
        

    #########################
    # DIVERS utilitaires    #
    #########################

    def set_logging_level(self, level:int):
        '''Change le niveau de log
        level = 10 (DEBUG), 20(INFO), 30(WARNING), 40(ERROR), 50(CRITICAL)
        '''
        #logging.basicConfig(level=level)
        self.logger.setLevel(level)
        if self.client:
            self.client.DEBUG = level <= logging.DEBUG
        logging.info(f"Logging level updated to : {logging.getLevelName(level)}")

    def get_topic(self, topic:str)-> str:
        '''Ajout base_topic quand './' devant
        '''
        if self.mqtt_base_topic and topic[:2]=="./":
            return self.mqtt_base_topic + topic[2:]
        else:
            return topic

    @staticmethod
    def led_function(led: None | int | machine.Pin)-> function:
        '''Renvoie une fonction qui pilote une led
        (intéret : led peut être None ou int ou Pin)
        '''
        if led is None : return lambda _:None
        if type(led)!=machine.Pin:
            led = machine.Pin(led)
        led.init(machine.Pin.OUT,value = 0)
        def func(v:bool):
            led(v)
        return func

    async def pulse(self):
        ''' Pulses incoming LED each time a subscribed msg arrives.
        '''
        self.led_incoming(True)
        await asyncio.sleep(self.incoming_pulse_duration)
        self.led_incoming(False)

    @staticmethod
    def to_str(value:any)->str:
        '''renvoie un string, éventuellement formaté en json
        '''
        if type(value)==str:
            return value
        else:
            return json.dumps(value)
        

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
                callbacks = self.callbacks[topic]
                for callback in callbacks or []:
                    asyncio.create_task(callback(topic, payload))
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
        if topic is not None and payload is not None:
            logging.info(f'publish {topic} : {payload}')
            asyncio.create_task(self.client.publish(self.get_topic(topic), self.to_str(payload), qos = qos))

    async def publish_async(self, topic:str, payload:str, qos = 0):
        if topic is not None and payload is not None:
            logging.info(f'publish_async {topic} : {payload}')
            await self.client.publish(self.get_topic(topic), self.to_str(payload), qos = qos)

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
        self.callbacks[topic]=self.callbacks.get(topic, [])
        self.callbacks[topic].append(callback)

    def add_topic(self, topic:Topic):
        '''Add a new topic
        - subscribe to reverse topic
        '''
        # Subscribe read function for reverse topic
        if topic.reverse_topic() :
            async def callback(_topic, _payload):
                await self.publish_async(
                    str(topic),
                    await topic.get_payload_async(_topic, _payload))
            self.subscribe(
                topic.reverse_topic(),
                callback
                )
        # Subscribe action function for topic
        if topic.on_incoming:
            async def callback(_topic, _payload):
                logging.debug(f"Callback action : {_topic=} , {_payload=}")
                payload = await topic.do_action_async(_topic,_payload)
                logging.debug(f"payload = {payload}")
                if topic.reverse_topic_action():
                    await self.publish_async(topic.reverse_topic_action(),payload)
            self.subscribe(
                str(topic),
                callback
                )
            
        # Add routine for auto send topics
        if topic.is_auto_send():
            self.add_routine(topic.get_routine(self.publish_async))
            if topic.send_period_as_param:
                self.params.set_param(f"send_period {topic}", default=topic.send_period, on_change= lambda period : topic.set_send_period(period))

        # Essentiellement pour IRQ
        topic.attach(self)
        # Essentiellement pour webserver
        self.topics.append(topic)

    #########################
    # Routines autres       #
    #########################

    def add_routine(self, routine:TopicRoutine|callable):
        '''Ajoute une routine qui sera executée dans le main comme tache
        '''
        if isinstance(routine, Topic):
            self.routines.append(routine.do_action_async)
            logging.info(f"New routine added for Toppic {routine}")
        elif callable(routine):
            self.routines.append(routine)
            logging.info(f"New routine added for callable {routine}")
        else:
            logging.error(f"{routine} is not a Topics and not callable.")

    #########################
    # Main                  #
    #########################

    async def main(self):
        ''' Connect au broker, puis crée l'ensemble des taches asynchrones.
        Et attend indéfiniment qu'elles terminent.
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
                if self.on_fail_connect:
                    try:
                        await self.on_fail_connect()
                    except TypeError:
                        pass

        logging.info(f"SYSINFO :  {await self.sysinfo()}")
        tasks = []
        for task in (self.up, self.down, self.messages, self.garbage_collector_async, self.get_rtc_async):
            tasks.append(asyncio.create_task(task()))
        if self.wd:
            tasks.append(asyncio.create_task(self.hardware_watchdog_async()))

        for task in self.routines:
            try:
                tasks.append(asyncio.create_task(task()))
            except Exception as e:
                logging.error(f"Error on task {task} : {e}")

        #Web interface
        if self.web:
            tasks.append(self.get_web_task())
        

        #Attente infinie
        for task in tasks:
            await task #Mais on peut attendre ... indéfiniement.


    def run(self, wait:int=0):
        if wait:
            print("Wait 5 seconds before starting the IoT")
            time.sleep(wait)
        '''Lance la boucle principale'''
        if self.watchdog:
            self.init_watchdog(self.watchdog)
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
                    send_period=watchdog_delai//5,
                    reverse_topic=False,
                    read=lambda topic, payload:"FEED",
                    on_incoming=lambda topic, payload: self.wd.feed(),
                    send_period_as_param=False
                    ))
    
    async def hardware_watchdog_async(self):
        '''Create async hardware watchdog
        '''
        wd = machine.WDT(timeout=8388)
        while True:
            await asyncio.sleep(1)
            wd.feed()
            #logging.debug("hardware watchdog feeded.")

    @staticmethod
    async def garbage_collector_async(period=30):
        '''Routine for permanent garbage collector
        '''
        while True:
            await asyncio.sleep(period)
            before = gc.mem_alloc()
            gc.collect()
            logging.debug(f"garbage collector : {before - gc.mem_alloc()} bytes saved.")

    def init_system_topics(self, period:int):
        '''Create system topics
        '''
        self.add_topic(Topic(
                    "./SYSINFO",
                    send_period=period,
                    read=self.sysinfo,
                    send_period_as_param=False
                    ))
        self.add_topic(Topic(
                    "./SET_PARAMS",
                    reverse_topic=False,
                    on_incoming= lambda topic, payload : self.params.set_params(payload)
        ))
        self.add_topic(Topic(
                    "./SET_PARAM",
                    reverse_topic=False,
                    on_incoming= lambda topic, payload : self.params.set_param(topic, payload)
        ))
        self.add_topic(Topic(
                    "./PARAMS",
                    read = self.params.get_params
        ))
        self.add_topic(Topic(
                    "/FmPyIOT/datetime_",
                    send_period=3600, #toutes les heures
                    read = lambda topic, payload : "_",
                    reverse_topic=False,
                    send_period_as_param=False
                     ))
        self.add_topic(Topic(
                    "/FmPyIOT/datetime",
                    reverse_topic=False,
                    on_incoming= self.set_rtc
                     ))
        #self.add_topic(Topic('./LOGS',
        #            read = self.get_logs
        #))

    async def get_rtc_async(self):
        while not self.rtc_is_updated:
            await self.publish_async("/FmPyIOT/datetime_","_")
            await asyncio.sleep(10)
            
    def get_vsys(self)->float:
        '''renvoie le voltage VSYS
        '''
        wlan_active = self.wlan.active()
        self.wlan.active(False)
        machine.Pin(25, mode = machine.Pin.OUT, pull = machine.Pin.PULL_DOWN).high()
        machine.Pin(29, machine.Pin.IN)
        vsys = machine.ADC(29).read_u16()
        #machine.Pin(29, machine.Pin.ALT, pull=machine.Pin.PULL_DOWN, alt=7)
        self.wlan.active(wlan_active)
        return vsys * 3 * 3.3 / 65535
    
    async def sysinfo(self)->dict:
        '''renvoie les informations system
        '''
        statvfs_keys = ['f_bsize ', 'f_frsize ', 'f_blocks', 'f_bfree', 'f_bavail', 'f_files', 'f_ffree', 'f_favail', 'f_flag', 'fnamemax']
        ifconfig_keys = ['ip', 'subnet', 'gateway', 'dns']
        uname_keys = ['sysname', 'nodename', 'release', 'version', 'machine']
        gc.collect()
        wifi = {k:self.wlan.config(k) for k in ['ssid', 'channel', 'txpower']}
        wifi['rssi'] = self.wlan.status('rssi')
        return{
            'name' : self.name,
            'mqtt_base_topic' : self.mqtt_base_topic,
            #'description' : self.description,
            'uname' : dict(zip(uname_keys, list(os.uname()))),
            'ifconfig' : dict(zip(ifconfig_keys, self.wlan.ifconfig())),
            'wifi' : wifi,
            'mac' : ubinascii.hexlify(self.wlan.config('mac'),':').decode(),
            'mem_free' : gc.mem_free(),
            'mem_alloc' : gc.mem_alloc(),
            'statvfs' : dict(zip(statvfs_keys,os.statvfs('/'))),
            'logging_level' : logging.root.level,
            'vsys' : self.get_vsys(),
            'mqtt_client_id' : self.client._client_id
        }
    
    def add_param(self, param:FmPyIotParam):
        '''Ajout un paramètre à l'iot
        Non utilisé TODO
        '''
        self.params.append(param)
    
    def set_param(self, key:bytes, payload:any=None, default:bytes|None=None, on_change:callable=None):
        self.params.set_param(key, payload, default, on_change)

    def get_param(self, topic:bytes) -> any:
        '''renvoie la valeur d'un paramètre
        Pour retro-compatibility
        '''
        return self.params.get_params().get(topic)

    def set_rtc_from_params(self):
        params = self.params.get_params()
        try:
            self.rtc.datetime(params['rtc'])
        except Exception as e:
            logging.error(str(e))

    def set_rtc(self, payload):
        rtc = tuple(json.loads(payload))
        self.rtc.datetime(rtc)
        self.params.set_param("rtc",json.dumps(rtc))
        logging.info(f"Set RTC {rtc}")
        self.rtc_is_updated = True

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
        '''place le dispositif en mode debug'''
        if self.wd:
            self.wd.disable()
            print('Watchdog desactivate')

    def get_logs(self, index=0):
        '''Renvoie le contenu d'un fichier log
        '''
        if self.log_file:
            file_name = self.log_file
            if index>0:
                file_name += f'.{index}'
            try:
                return open(file_name,'r').read()
            except OSError as e:
                logging.error(e)