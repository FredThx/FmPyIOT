import uasyncio as asyncio
import logging, os, json
from machine import Pin, reset as machine_reset, bootloader as machine_bootloader
from fmpyiot.fmpyiot import FmPyIot
from fmpyiot.repl import REPL
from fmpyiot.device import Device
from ubinascii import a2b_base64 as base64_decode
import nanoweb as naw
import uerrno

logging.basicConfig(level=logging.DEBUG)

class FmPyIotWeb(FmPyIot):
    '''Un objet connecté via mqtt et http
    '''

    assets_dir = "./fmpyiot/assets/"

    def __init__(self,
            mqtt_host:str, mqtt_base_topic:str = "",
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
            render_web:callable = None,
            led_wifi:Pin|int = None,
            led_incoming:Pin|int = None,
            incoming_pulse_duration:float = 0.3,
            keepalive:int = 120,
            on_fail_connect:callable = None,
            device:Device=None
                 ):
        super().__init__(
            mqtt_host=mqtt_host, mqtt_base_topic=mqtt_base_topic,
            ssid = ssid, password=password,
            autoconnect=False, watchdog=watchdog, sysinfo_period=sysinfo_period,
            logging_level = logging_level, led_wifi = led_wifi, led_incoming=led_incoming,
            name=name,description = description,
            incoming_pulse_duration = incoming_pulse_duration, keepalive=keepalive,
            on_fail_connect=on_fail_connect,
            device=device
            )
        if web:
            self.web = naw.Nanoweb(web_port)
            self.web_credentials = web_credentials
        self.render_web = render_web or (device.render_web if device else None)#Callable to render web page
        #Auto run
        if autoconnect:
            self.run()
        
    def get_web_task(self)-> asyncio.Task:
        self.REPL=REPL(size=20)
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
    async def send_response(request, code:int=200, message:str="OK", content_type:str=None, status:str=None):
        await request.write(f"HTTP/1.1 {code} {message}\r\n")
        if content_type:
            await request.write(f"Content-Type: {content_type}\r\n")
        await request.write("\r\n")
        if status:
            await request.write(f'{{"status": {status}}}')

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
        await FmPyIotWeb.send_response(request)
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
    
    @staticmethod
    def unquote(string:str)->str:
        """unquote('abc%20def') -> 'abc def'.

        Note: if the input is a str instance it is encoded as UTF-8.
        This is only an issue if it contains unescaped non-ASCII characters,
        which URIs should not.
        """
        if not string:
            return ""
        if isinstance(string, str):
            b_string = string.encode('utf-8')
        else:
            b_string = string
        bits = b_string.split(b'%')
        if len(bits) == 1:
            return string
        res = bytearray(bits[0])
        append = res.append
        extend = res.extend
        for item in bits[1:]:
            try:
                append(int(item[:2], 16))
                extend(item[2:])
            except KeyError:
                append(b'%')
                extend(item)
        return bytes(res).decode('utf-8')

    def init_web(self):
        '''Initialise le serveur web
        '''
        self.web.STATIC_DIR = self.assets_dir
        self.web.assets_extensions += ('ico',)

        @self.web.route("/")
        @self.authenticate()
        async def index(request):
            '''Page principale
            '''
            await FmPyIotWeb.send_response(request)
            await self.send_file(
                    request,
                    f'./{self.assets_dir}/index.html')

        @self.web.route('/api/topics')
        @self.authenticate()
        async def get_html_topics(request):
            '''Renvoie sous forme html la liste des topics et leurs valeurs, boutons actions, ....
            '''
            await FmPyIotWeb.send_response(request)
            for topic in self.topics:
                await request.write(topic.to_html())

        @self.web.route('/assets/*')
        @self.authenticate()
        async def assets(request):
            '''Permet un access aux fichiers static du site
            '''
            await FmPyIotWeb.send_response(request)
            args = {}
            filename = request.url.split('/')[-1]
            filename = FmPyIotWeb.unquote(filename)
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
            await FmPyIotWeb.send_response(request, content_type='application/json')
            topics = {}
            for topic in self.topics:
                payload = await topic.get_payload_async(topic.topic, None)
                if payload is not None:
                    topics[topic.topic] = {'payload' : payload, 'id': topic.get_id()}
            await request.write(json.dumps(topics))

        @self.web.route('/api/ls')
        @self.authenticate()
        async def api_ls(request):
            '''List device files (only on root)
            '''
            logging.debug(f"request={request}")
            await FmPyIotWeb.send_response(request, content_type='application/json')
            await request.write('{"files": [%s]}' % ', '.join(
                '"' + f + '"' for f in sorted(os.listdir('.')) if "." in f 
            ))

        @self.web.route('/api/download/*')
        @self.authenticate()
        async def api_download(request):
            '''Download file from device
            '''
            logging.debug(f"request={request}")
            filename = request.url[len(request.route.rstrip("*")) - 1:].strip("/")
            filename = FmPyIotWeb.unquote(filename)
            await FmPyIotWeb.send_response(request, content_type='application/octet-stream')
            await request.write(f"Content-Disposition: attachment; filename={filename}\r\n\r\n")
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
            filename = FmPyIotWeb.unquote(filename)
            try:
                os.remove(filename)
                logging.info(f"Delete file : {filename}")
            except OSError as e:
                raise naw.HttpError(request, 500, "Internal error")
            await self.send_response(request)

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
                await FmPyIotWeb.send_response(request, code=204, message="No Content")
                return
            output_file = request.url[len(request.route.rstrip("*")) - 1:].strip("\/")
            output_file = FmPyIotWeb.unquote(output_file)
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
            await self.send_response(request, 201, "Created")
            
        @self.web.route('/api/reboot')
        @self.authenticate()
        async def reboot(request):
            '''Reboot the device
            '''
            logging.debug(f"request={request}")
            logging.info("reboot device")
            await self.send_response(request, 200, "OK")
            machine_reset()
            

        @self.web.route('/api/bootloader')
        @self.authenticate()
        async def bootloader(request):
            '''Reset the device and enter its bootloader
            '''
            logging.debug(f"request={request}")
            logging.info("Reset the device and enter its bootloader")
            await self.send_response(request, 200, "OK")
            machine_bootloader()
            

        @self.web.route('/api/action/*')
        @self.authenticate()
        async def action(request):
            '''Execute l'action liés à un topic
            '''
            logging.debug(f"request={request}")
            data = await self.get_post_data(request)
            logging.debug(f"POST : data={data}")
            topic_id = request.url[len(request.route.rstrip("*")) - 1:].strip("\/")
            #topic_id = FmPyIotWeb.unquote(topic_id)
            topic_id = topic_id[7:]
            topics = [topic for topic in self.topics if topic.get_id()==topic_id]
            if not topics:
                logging.error(f"Erreur en lien avec topic.get_id() : {topic_id}=>{topics}")
                await self.send_response(request, 400, f"Erreur en lien avec topic.get_id() : {topic_id}=>{topics}")
                raise Exception("Erreur en lien avec topic.get_id()")
            topic = topics[0]
            await topic.do_action_async(data.get('topic'),data.get('payload'))
            await self.send_response(request, 200, 'ok')

        @self.web.route('/api/repl')
        @self.authenticate()
        async def repl(request):
            '''renvoie les dernières ligne du REPL
            '''
            if request.method != "GET":
                raise naw.HttpError(request, 501, "Not Implemented")
            new_lines = self.REPL.read()
            await FmPyIotWeb.send_response(request, content_type="application/json")
            await request.write(json.dumps({'repl' : new_lines}))
        
        @self.web.route('/api/repl/cmd')
        @self.authenticate()
        async def repl(request):
            '''Envoie une commande python au REPL
            '''
            if request.method != "POST":
                raise naw.HttpError(request, 501, "Not Implemented")
            try:
                data = await self.get_post_data(request)
                cmd = data['cmd']
            except:
                raise naw.HttpError(request, 400, "Bad request")
            rep = await self.REPL.exec(cmd)
            await FmPyIotWeb.send_response(request, content_type="application/json")
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
            await self.send_response(request)

        @self.web.route('/api/hello')
        async def hello(request):
            await FmPyIotWeb.send_response(request)
            await request.write(f"FmPyIOT/{self.name}")

        @self.web.route('/api/logs')
        async def api_get_logs(request):
            '''Renvoie le contenu du dernier fichier log
            '''
            await FmPyIotWeb.send_response(request)
            await request.write(f"{self.get_logs(0)}")
        
        @self.web.route('/api/params')
        @self.authenticate()
        async def get_html_params(request):
            '''Renvoie sous forme html la liste des params et leurs valeurs
            '''
            await FmPyIotWeb.send_response(request)
            for html_param in self.params.to_html():
                await request.write(html_param)

        @self.web.route('/api/params/delete/*')
        @self.authenticate()
        async def delete_params(request):
            '''Supprime tous les paramètres
            '''
            if request.method != "DELETE":
                raise naw.HttpError(request, 501, "Not Implemented")
            param = request.url[len(request.route.rstrip("*")) - 1:].strip("\/")
            param = self.unquote(param)
            if self.params.delete_param(param):
                await self.send_response(request, 200, "OK")
            else:
                await self.send_response(request, 204, "No Content")

        @self.web.route('/api/render_web')
        @self.authenticate()
        async def render_web(request):
            '''Renvoie le contenu de la page web générée par la fonction render_web
            '''
            await FmPyIotWeb.send_response(request)
            if self.render_web:
                content = self.render_web()
                await request.write(content)
            else:
                await request.write(f"{self.description}")


