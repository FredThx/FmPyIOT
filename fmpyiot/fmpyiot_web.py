import uasyncio as asyncio
import logging, os, ubinascii, gc, json, network
from machine import Pin, reset as machine_reset
from fmpyiot.fmpyiot import FmPyIot
from fmpyiot.topics import Topic, TopicRoutine
from fmpyiot.wd import WDT
from fmpyiot.repl import REPL
from ubinascii import a2b_base64 as base64_decode
import nanoweb as naw
import uerrno

logging.basicConfig(level=logging.DEBUG)

class FmPyIotWeb(FmPyIot):
    '''Un objet connecté via mqtt et http
    '''

    assets_dir = "./fmpyiot/assets/"

    def __init__(self,
            mqtt_host:str, mqtt_base_topic:str = None,
            ssid:str = None, password:str = None,
            autoconnect:bool = False,
            watchdog:int = 100,
            sysinfo_period:int = 600, #s
            logging_level = logging.DEBUG,
            web:bool = True,
            web_port:int = 80,
            web_credentials:tuple[str,str] = None,
            name:str = "MyFmPyIot",
            description:str= "Un objet connecté à base de micropython et de FmPyiot.",
            led_wifi:Pin|int = None,
            led_incoming:Pin|int = None,
            incoming_pulse_duration:float = 0.3,
            keepalive:int = 120,
                 ):
        super().__init__(
            mqtt_host=mqtt_host, mqtt_base_topic=mqtt_base_topic,
            ssid = ssid, password=password,
            autoconnect=False, watchdog=watchdog, sysinfo_period=sysinfo_period,
            logging_level = logging_level, led_wifi = led_wifi, led_incoming=led_incoming,
            incoming_pulse_duration = incoming_pulse_duration, keepalive=keepalive)
        self.name = name
        self.description = description
        if web:
            self.web = naw.Nanoweb(web_port)
            self.web_credentials = web_credentials
        #Auto run
        if autoconnect:
            self.run()
        
    def get_web_task(self)-> asyncio.Task:
        self.REPL=REPL()
        self.init_web()
        return asyncio.create_task(self.web.run())


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
                '"' + f + '"' for f in sorted(os.listdir('.')) if "." in f 
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