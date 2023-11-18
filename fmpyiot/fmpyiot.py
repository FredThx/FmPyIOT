from mqtt_as.mqtt_as import MQTTClient, config as mqtt_as_config
import uasyncio as asyncio
import logging, os, ubinascii, gc, json, network
from machine import Pin, reset as machine_reset
from fmpyiot.topics import Topic, TopicRoutine
from fmpyiot.wd import WDT
from fmpyiot.repl import REPL
from ubinascii import a2b_base64 as base64_decode
import nanoweb as naw
import uerrno

logging.basicConfig(level=logging.DEBUG)

class FmPyIot:
    '''Un objet connecté via mqtt et http
    '''
    def __init__(self,
            mqtt_host:str, mqtt_client_name:str = None, mqtt_base_topic:str = None,
            ssid:str = None, password:str = None,
            autoconnect:bool = False,
            watchdog:int = 100,
            debug:bool = True,
            sysinfo_period:int = 600, #s
            country:str = 'FR',
            logging_level = logging.DEBUG,
            mqtt_log:str = "./LOG",
            log_console_level:int = logging.DEBUG,
            log_mqtt_level:int = logging.INFO,
            web:bool = False,
            web_port:int = 80,
            web_credentials:tuple[str,str] = None,
            name:str = "MyFmPyIot",
            description:str= "Un objet connecté à base de micropython et de FmPyiot.",
            led_wifi:Pin|int = None,
            led_incoming:Pin|int = None,
            incoming_pulse_duration:float = 0.3,
            keepalive:int = 120,
                 ):
        self.routines:list[TopicRoutine] = []
        self.topics:list[Topic]= []
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
        #MQTTClient.DEBUG = True
        self.client = MQTTClient(mqtt_as_config)
        self.wlan = self.client._sta_if
        self.callbacks = {} #{'topic' : callback}
        #Logging level
        self.set_logging_level(logging_level)
        #Watchdog
        self.wd = None
        if watchdog:
            self.init_watchdog(watchdog)
        if sysinfo_period:
            self.init_system_topics(sysinfo_period)
        self.params_loaders = []
        #Web
        self.name = name
        self.description = description
        if web:
            self.web = naw.Nanoweb(web_port)
            self.web_credentials = web_credentials
        #Auto run
        if autoconnect:
            self.run()
        

    #########################
    # DIVERS utilitaires    #
    #########################

    def set_logging_level(self, level:int):
        '''Change le niveau de log
        level = 10 (DEBUG), 20(INFO), 30(WARNING), 40(ERROR), 50(CRITICAL)
        '''
        logging.basicConfig(level=level)
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
                callback = self.callbacks[topic]
                if callback:
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
        self.callbacks[topic]=callback

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
        if topic.action:
            async def callback(_topic, _payload):
                logging.debug("Callback action")
                payload = await topic.do_action_async(_topic,_payload)
                logging.debug(f"payload = {payload}")
                await self.publish_async(topic.reverse_topic_action(),payload)
            self.subscribe(
                str(topic),
                callback
                )
        # Add routine for auto send topics
        if topic.is_auto_send():
            async def _send_topic_async():
                while True:
                    await topic.send_async(self.publish_async)
            self.add_routine(_send_topic_async)

        # Essentiellement pour IRQ
        topic.attach(self)
        # Essentiellment pour webserver
        self.topics.append(topic)

    #########################
    # Routines autres       #
    #########################

    def add_routine(self, routine:TopicRoutine|callable):
        '''Ajoute une routine qui sera executée dans le main comme tache
        '''
        if isinstance(routine, Topic):
            self.routines.append(routine.do_action_async)
        elif callable(routine):
            self.routines.append(routine)
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
        logging.info(f"SYSINFO :  {await self.sysinfo()}")
        tasks = []
        for task in (self.up, self.down, self.messages):
            tasks.append(asyncio.create_task(task()))
        for task in self.routines:
            tasks.append(asyncio.create_task(task()))

        #Web interface
        if self.web:
            #REPL
            self.REPL=REPL()
            self.init_web()
            tasks.append(asyncio.create_task(self.web.run()))

        #Attente infinie
        for task in tasks:
            await task #Mais on peut attendre ... indéfiniement.


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
            'name' : self.name,
            'description' : self.description,
            'uname' : list(os.uname()),
            'ifconfig' : self.wlan.ifconfig(),
            'wifi' : {k:self.wlan.config(k) for k in ['ssid', 'channel', 'txpower']},
            'mac' : ubinascii.hexlify(self.wlan.config('mac'),':').decode(),
            'mem_free' : gc.mem_free(),
            'mem_alloc' : gc.mem_alloc(),
            'statvfs' : os.statvfs('/'),
            'logging_level' : logging.root.level,
        }

    params_json = "params.json"

    def get_params(self)->dict:
        '''Renvoie le contenu de params_json
        '''
        try:
            with open(self.params_json,"r") as json_file:
                return json.load(json_file)
        except OSError as e:
            logging.warning(f"Error reading {self.params_json} : {e}")
            logging.info(f"create new empty file {self.params_json}")
            self.write_params({})

    
    def set_params(self, topic:bytes, payload:bytes):
        '''Met à jour le fichier params_json en fonction de payload
        '''
        params = self.get_params()
        try:
            params.update(json.loads(payload))
        except Exception as e:
            logging.error(f"Error reading file {self.params_json} : {e}")
        self.write_params(params)
        for loader in self.params_loaders:
            try:
                loader()
            except Exception as e:
                print(f"Error on params_loader {loader} : {e}")
    
    def write_params(self, params):
        '''Ecrit le fichier params
        '''
        try:
            with open(self.params_json,"w") as json_file:
                json.dump(params, json_file)
        except OSError as e:
            logging.error(f"Error writing file {self.params_json} : {e}")
    
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
        '''place le dispositif en mode debug'''
        self.wd.disable()
        print('Watchdog desactivate')

########################
#  WEB SERVER        ###
########################
    assets_dir = "./fmpyiot/assets/"

    def authenticate(self):
        '''Décorateur pour BASIC authentification (self.web_credentials)
        '''
        async def fail(request):
            await request.write("HTTP/1.1 401 Unauthorized\r\n")
            await request.write('WWW-Authenticate: Basic realm="Restricted"\r\n\r\n')
            await request.write("<h1>Unauthorized</h1>")

        def decorator(func):
            async def wrapper(request):
                header = request.headers.get('Authorization', None)
                if header is None:
                    return await fail(request)

                # Authorization: Basic XXX
                kind, authorization = header.strip().split(' ', 1)
                if kind != "Basic":
                    return await fail(request)

                authorization = base64_decode(authorization.strip()) \
                    .decode('ascii') \
                    .split(':')

                if self.web_credentials and list(self.web_credentials) != list(authorization):
                    return await fail(request)

                return await func(request)
            return wrapper
        return decorator


    @staticmethod
    async def api_send_response(request, code=200, message="OK"):
        await request.write("HTTP/1.1 %i %s\r\n" % (code, message))
        await request.write("Content-Type: application/json\r\n\r\n")
        await request.write('{"status": true}')

    @staticmethod
    async def send_file(request, filename, segment=64, binary=False):
        try:
            with open(filename, 'rb' if binary else 'r') as f:
                while True:
                    data = f.read(segment)
                    if not data:
                        break
                    await request.write(data)
        except OSError as e:
            if e.args[0] != uerrno.ENOENT:
                raise
            raise naw.HttpError(request, 404, "File Not Found")
    @staticmethod
    async def get_post_data(request):
        """ get Post data 
        """
        await request.write("HTTP/1.1 200 Ok\r\n")
        if request.method != "POST":
            raise naw.HttpError(request, 501, "Not Implemented")
        try:
            content_length = int(request.headers['Content-Length'])
            content_type = request.headers['Content-Type']
        except KeyError:
            raise naw.HttpError(request, 400, "Bad Request")
        data = (await request.read(content_length)).decode()
        if content_type == 'application/json':
            result = json.loads(data)
        elif content_type.split(';')[0] == 'application/x-www-form-urlencoded':
            result = {}
            for chunk in data.split('&'):
                key, value = chunk.split('=', 1)
                result[key]=value
        return result

    def init_web(self):
        '''Initialise un serveur web par defaut
        '''
        self.web.STATIC_DIR = self.assets_dir
        self.web.assets_extensions += ('ico',)

        @self.web.route("/")
        @self.authenticate()
        async def index(request):
            '''Page principale
            '''
            await request.write("HTTP/1.1 200 OK\r\n\r\n")
            await self.send_file(
                    request,
                    f'./{self.assets_dir}/index.html')

        @self.web.route('/api/topics')
        @self.authenticate()
        async def get_html_topics(request):
            '''Renvoie sous forme html la liste des topics et leurs valeurs, boutons actions, ....
            '''
            await request.write("HTTP/1.1 200 OK\r\n\r\n")
            await request.write(self.get_html_topics())

        @self.web.route('/assets/*')
        @self.authenticate()
        async def assets(request):
            '''Permet un access aux fichiers static du site
            '''
            await request.write("HTTP/1.1 200 OK\r\n")
            args = {}
            filename = request.url.split('/')[-1]
            if filename.endswith('.png'):
                args = {'binary': True}
            await request.write("\r\n")
            await self.send_file(
                request,
                './%s/%s' % (self.assets_dir, filename),
                **args,
            )

        @self.web.route('/api/status')
        @self.authenticate()
        async def api_status(request):
            '''API qui va renvoyer (json) le status avec toutes les valeurs des topics
            '''
            logging.debug(f"request={request}")
            await request.write("HTTP/1.1 200 OK\r\n")
            await request.write("Content-Type: application/json\r\n\r\n")
            topics = {}
            for topic in self.topics:
                payload = await topic.get_payload_async(topic.topic, None)
                if payload:
                    topics[topic.topic] = {'payload' : payload, 'id': topic.get_id()}
            await request.write(json.dumps(topics))

        @self.web.route('/api/ls')
        @self.authenticate()
        async def api_ls(request):
            '''List device files (only on root)
            '''
            logging.debug(f"request={request}")
            await request.write("HTTP/1.1 200 OK\r\n")
            await request.write("Content-Type: application/json\r\n\r\n")
            await request.write('{"files": [%s]}' % ', '.join(
                '"' + f + '"' for f in sorted(os.listdir('.'))
            ))

        @self.web.route('/api/download/*')
        @self.authenticate()
        async def api_download(request):
            '''Download file from device
            '''
            logging.debug(f"request={request}")
            await request.write("HTTP/1.1 200 OK\r\n")
            filename = request.url[len(request.route.rstrip("*")) - 1:].strip("/")
            await request.write("Content-Type: application/octet-stream\r\n")
            await request.write("Content-Disposition: attachment; filename=%s\r\n\r\n"
                                % filename)
            logging.info(f"Download file : {filename}")
            await naw.send_file(request, filename)

        @self.web.route('/api/delete/*')
        @self.authenticate()
        async def api_delete(request):
            '''Delete file on device
            '''
            logging.debug(f"request={request}")
            if request.method != "DELETE":
                raise naw.HttpError(request, 501, "Not Implemented")
            filename = request.url[len(request.route.rstrip("*")) - 1:].strip("\/")
            try:
                os.remove(filename)
                logging.info(f"Delete file : {filename}")
            except OSError as e:
                raise naw.HttpError(request, 500, "Internal error")
            await self.api_send_response(request)

        @self.web.route('/api/upload/*')
        @self.authenticate()
        async def upload(request):
            '''Upload file to device
            '''
            logging.debug(f"request={request}")
            if request.method != "PUT":
                raise naw.HttpError(request, 501, "Not Implemented")
            bytesleft = int(request.headers.get('Content-Length', 0))
            if not bytesleft:
                await request.write("HTTP/1.1 204 No Content\r\n\r\n")
                return
            output_file = request.url[len(request.route.rstrip("*")) - 1:].strip("\/")
            tmp_file = output_file + '.tmp'
            try:
                with open(tmp_file, 'wb') as o:
                    while bytesleft > 0:
                        chunk = await request.read(min(bytesleft, 64))
                        o.write(chunk)
                        bytesleft -= len(chunk)
                    o.flush()
            except OSError:
                raise naw.HttpError(request, 500, "Internal error")
            try:
                os.remove(output_file)
            except OSError:
                pass
            try:
                os.rename(tmp_file, output_file)
            except OSError:
                raise naw.HttpError(request, 500, "Internal error")
            logging.info(f"File uploaded : {output_file}")
            await self.api_send_response(request, 201, "Created")
            
        @self.web.route('/api/reboot')
        @self.authenticate()
        async def reboot(request):
            '''Upload file to device
            '''
            logging.debug(f"request={request}")
            logging.info("rebbot device")
            machine_reset()
            await self.api_send_response(request, 200, "OK")

        @self.web.route('/api/action/*')
        @self.authenticate()
        async def action(request):
            '''Execute l'action liés à un topic
            '''
            logging.debug(f"request={request}")
            data = await self.get_post_data(request)
            logging.debug(f"POST : data={data}")
            topic_id = request.url[len(request.route.rstrip("*")) - 1:].strip("\/")
            topic_id = topic_id[7:]
            topics = [topic for topic in self.topics if topic.get_id()==topic_id]
            if not topics:
                logging.error(f"Erreur en lien avec topic.get_id() : {topic_id}=>{topics}")
                await self.api_send_response(request, 400, f"Erreur en lien avec topic.get_id() : {topic_id}=>{topics}")
                raise Exception("Erreur en lien avec topic.get_id()")
            topic = topics[0]
            await topic.do_action_async(data.get('topic'),data.get('payload'))
            await self.api_send_response(request, 200, 'ok')

        @self.web.route('/api/repl')
        @self.authenticate()
        async def repl(request):
            '''renvoie les dernières ligne du REPL
            '''
            if request.method != "GET":
                raise naw.HttpError(request, 501, "Not Implemented")
            new_lines = self.REPL.read()
            await request.write("HTTP/1.1 200 OK\r\n")
            await request.write("Content-Type: application/json\r\n\r\n")
            await request.write(json.dumps({'repl' : new_lines}))
        
        @self.web.route('/api/repl/cmd')
        @self.authenticate()
        async def repl(request):
            '''renvoie les dernières ligne du REPL
            '''
            if request.method != "POST":
                raise naw.HttpError(request, 501, "Not Implemented")
            try:
                data = await self.get_post_data(request)
                cmd = data['cmd']
            except:
                raise naw.HttpError(request, 400, "Bad request")
            rep = await self.REPL.exec(cmd)
            await request.write("HTTP/1.1 200 OK\r\n")
            await request.write("Content-Type: application/json\r\n\r\n")
            await request.write(json.dumps({'rep' : rep}))
            

        @self.web.route('/api/logging-level/*')
        @self.authenticate()
        async def logging_level(request):
            if request.method != "POST":
                raise naw.HttpError(request, 501, "Not Implemented")
            try:
                level = int(request.url[len(request.route.rstrip("*")) - 1:].strip("\/"))
            except:
                raise naw.HttpError(request, 400, "Bad request")
            self.set_logging_level(level)
            await self.api_send_response(request)

        @self.web.route('/api/hello')
        async def hello(request):
            await request.write("HTTP/1.1 200 OK\r\n\r\n")
            await request.write(f"FmPyIOT/{self.name}")
    
    def get_html_topics(self)->str:
        '''renvoie du code html
        '''
        html = "".join([topic.to_html() for topic in self.topics])
        return html
    

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