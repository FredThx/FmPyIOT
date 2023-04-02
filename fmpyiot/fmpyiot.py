import os, network, time, json, gc, _thread
import logging
import rp2
from machine import Timer
from fmpyiot.wd import WDT
from fmpyiot.umqtt.simple import MQTTClient
from fmpyiot.topics import Topic
from fmpyiot.uping import ping
from fmpyiot.fwebiot import FwebIot
#from fmpyiot.flog_iot import FLogIot
import ubinascii

class  FmPyIot:
    ''' Un object connecté à base de micro python
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
            log_mqtt_level = logging.INFO

            ):
        '''Initialisation
        mqtt_host           :     mqtt host (ip or name)
        mqtt_client_name    :     (optional) mqtt client name (default : nodename+mac)
        mqtt_base_topic     :     (optional) mqtt base topic : added to all topics starting with "./"
        ssid                :       wifi SSID
        password            :       wifi password
        callback            :       function called with all incoming messages. args : topic, payload
        timeout             :       (seconds) for wifi connection
        watchdog            :       optional (seconds)
        mqtt_check_period   :       (default : 1s) : interval de temps entre deux vérification de messages mqtt
        debug             :       False : no debug print
        sysinfo_period  :       temps entre deux envoi des info systems
        country             :       for wifi (default : 'FR')
        async_mode          :       True : pub, sub managed by timer
                                    False : pub, sub, manage by run()
        mqtt_log            :       mqtt topic for logs (default : './LOG')
        log_echo            :       if True, print also logs on stdout
        '''
        rp2.country(country)
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.config(pm = 0xa11140) #disable power-saving mode
        self.ssid = ssid
        self.password = password
        self.timeout = timeout
        if mqtt_client_name is None:
            mqtt_client_name = f"{os.uname().nodename}-{self.wlan.config('mac')}"
        self.mqtt_sub = MQTTClient(f"{mqtt_client_name}_sub", mqtt_host, keepalive=7200)
        self.mqtt_pub = MQTTClient(f"{mqtt_client_name}_pub", mqtt_host, keepalive=7200)
        self.mqtt_sub.set_callback(self.on_mqtt_message)
        self.mqtt_base_topic = mqtt_base_topic + "/" if mqtt_base_topic[-1]!="/" else ""
        self.mqtt_check_period = mqtt_check_period
        self.callback = callback
        self.callbacks = {} #{topic:callback, ...}
        self.debug = debug
        self.auto_send_topics = []
        self.stopped = False
        self.timer = None
        #self.logger = FLogIot(self, log_console_level, log_mqtt_level, mqtt_log)
        if async_mode:
            self.timer=Timer(-1)
        #Connect
        if autoconnect:
            self.connect()
        #Watchdog
        self.wd = None
        if watchdog:
            self.init_watchdog(watchdog)
        if sysinfo_period:
            self.init_system_topics(sysinfo_period)
        #Interface web
        self.fwebiot = FwebIot(iot=self)

    def connect(self):
        self.logging("Try to connect IOT")
        if self.wifi_connect():
            try:
                self.logging("Try to connect to mqtt broker")
                self.mqtt_sub.connect()
                self.mqtt_pub.connect()
            except OSError:
                return False
            else:
                self.logging("mqtt connected.")
                self.resubscribe_all()
                if self.timer:
                    self.lock_timer=False
                    self.timer.init(mode = Timer.PERIODIC, period = self.mqtt_check_period, callback =self.on_timer)
                return True
        else:
            self.logging("Error Wifi not connected.")

    def on_timer(self, tim:Timer):
        '''Function call every self.mqtt_check_period ms
        Check messages from mqtt broker.
            if connection lost, retry to connect
        '''
        if not self.stopped:
            if not self.lock_timer:
                self.lock_timer=True
                self.do_mqtt_events()
                self.lock_timer=False
    
    def run(self):
        '''if async mode, start the timer
        else, loop forever
        '''
        self.stopped = False
        if self.timer:
            self.lock_timer=False
            self.timer.init(mode = Timer.PERIODIC, period = self.mqtt_check_period, callback =self.on_timer)
        else:
            while not self.stopped:
                self.do_mqtt_events()
                self.fwebiot.listen()
                time.sleep_ms(self.mqtt_check_period)


    def do_mqtt_events(self):
        '''Check incoming mqtt message and send topics messages
        '''
        if not self.check_wlan():
            self.connect()
        try:
            self.mqtt_sub.check_msg()
        except OSError as e:
            self.logging(f"Error during check_msg : {e}.\n Try to reconnect...")
            if self.timer:
                self.timer.deinit()
            time.sleep(10)
            self.connect()
        else:
            #self.logging("check_msg ok ")
            for topic in self.auto_send_topics:
                topic.auto_send(self.publish_topic)

    def wifi_connect(self):
        if self.wlan.isconnected():
            self.logging("wifi already connected.")
            return True
        else:
            self.logging(f"Try to connect WIFI {self.ssid}")
            #bssids = [ap[1] for ap in self.wlan.scan() if ap[0].decode()==self.ssid]
            #self.logging(f"Found {len(bssids)} bssi.")
            #for bssid in bssids:
            self.wlan.connect(self.ssid,self.password)#, bssid = bssid)
            #self.logging(f"Connection ({self.ssid} - {bssid}) en cours .", end="")
            timeout = time.time() + self.timeout
            while not self.wlan.isconnected() and time.time() < timeout:
                self.logging(".",end="")
                time.sleep(1)
            if self.wlan.isconnected():
                self.logging("WIFI connected.")
                return True
            else:
                self.wlan.disconnect()
                self.logging(f"Erreur : {self.str_network_status()}")

    def stop(self, stopped = True):
        self.stopped = stopped

    def get_topic(self, topic:str)-> str:
        '''Ajout base_topic quand './' devant
        '''
        if self.mqtt_base_topic and topic[:2]=="./":
            return self.mqtt_base_topic + topic[2:]
        else:
            return topic

    def publish_topic(self, topic:Topic):
        '''publish
        '''
        self.publish(str(topic),topic.get_payload())

    def publish(self, topic:str, payload:any):
        '''publish msg to mqtt broker
        '''
        if topic and payload is not None:
            topic = self.get_topic(topic)
            payload = json.dumps(payload)
            self.logging(f"publish {topic}=>{payload}")
            try:
                self.mqtt_pub.ping()
            except OSError:
                self.connect()
            finally:
                self.mqtt_pub.publish(topic, payload)
    

    def subscribe(self, topic:str, callback:function = None):
        '''Subscibe to a mqtt topic 
        callback : function(topic, payload)
        '''
        topic = self.get_topic(topic)
        self.logging(f"Subscribe {topic} : callback={callback}")
        try:
            self.mqtt_sub.ping()
        except Exception as e:
            self.logging("Error : mqtt not connected.")
        else:
            self.mqtt_sub.subscribe(topic)
        if callback:
            self.callbacks[bytes(topic,'utf-8')]=callback

    def resubscribe_all(self):
        '''Re-crée les subscriptions auprès du broker
        '''
        for topic, callback in self.callbacks.items():
            self.logging(f"resubscribe {topic}")
            self.mqtt_sub.subscribe(topic)

    def on_mqtt_message(self, topic, payload):
        '''on receive mqtt message
        '''
        self.logging(f"Reception de {topic}=>{payload}")
        if self.callback:
            self.callback(topic, payload)
        if topic in self.callbacks:
            self.callbacks[topic](topic, payload)
    
    def logging(self, txt, end = '\n'):
        if self.debug:
            print(txt,end=end)

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

    def sysinfo(self)->dict:
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
    
    def set_params(self, topic, payload):
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
    
    def check_wlan(self):
        '''Check wlan status (ping on mqtt) and kill wlan if test fall
        return True is wlan is ok, False otherwise
        '''
        try:
            assert ping(self.mqtt_pub.server,count=3,quiet=True)[1]>0,"Wlan error"
        except Exception as e:
            print(e)
            self.wlan.deinit()
            self.wlan.active(True)
            return False
        else:
            return True

    @staticmethod
    def str_mqtt_status(mqtt_client):
        if mqtt_client:
            try:
                mqtt_client.ping()
            except Exception:
                return "Error"
            else:
                return "Ok"
        else:
            return "Non connected."

    def __repr__(self):
        repr = f"""FmPyIot({self.mqtt_base_topic})
                WIFI : {self.str_network_status()}
                MQTT_sub : {self.str_mqtt_status(self.mqtt_sub)}
                MQTT_pub : {self.str_mqtt_status(self.mqtt_pub)}
                WD : {self.wd}
                callbacks : \n"""
        for topic, callback in self.callbacks.items():
            repr += f"\t\t\t{topic}\n"
        return repr
    