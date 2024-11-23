import time, logging, re
from machine import Pin
import uasyncio as asyncio
from fmpyiot.buffer import BufferBits

def never_crash(fn):
    def never_crash_function(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            print(f"Error : {e}")
            #logging.error(e)
    return never_crash_function

class Topic:
    '''Topic (Device) on a FmPyIOT object
    '''
    def __init__(self, topic:str,
                 send_period:float = None,
                 reverse_topic:bool|str = True,
                 read:function = None,
                 action:function = None,
                 send_period_as_param:bool=True):
        '''Initialisation
        Arguments : 
            - topic (can start with ./ for relative topic name)
            - send_period : period (seconds) for auto send timer
            - functions overloaded (ex : read=lambda : 42)
                - read
                - action
        '''
        self.topic = topic
        self.send_period = send_period
        self.send_period_as_param = send_period_as_param
        self._reverse_topic = reverse_topic
        self.read = read
        self.action = action
        self.last_send = 0
        self.sleep_mode = False

    def __str__(self)->str:
        return self.topic

    def is_auto_send(self)->bool:
        return self.send_period is not None
    
    def set_send_period(self, period:float|str):
        try:
            self.send_period = float(period)
        except ValueError as e:
            logging.error(f"set_send_period error : {e}")

    @never_crash
    def do_action(self, topic:str=None, payload:str=None)->str:
        '''Execute the action method and return (if exist) the value
        action function can accept arguments : (inital topic, initial payload), just initial payload or nothing
        '''
        # la fonction action pour prendre 2,1 ou 0 arguments
        # Et je n'ai pas trouvé comment connaitre en micropython le nombre d'arguments
        # Il existe la lib inspect, mais elle ne fonctionne pas avec les lambda function!
        logging.debug(f"do_action[{self}]({topic},{payload})...")
        if self.action:
            try:
                return self.action(topic, payload)
            except TypeError as e:
                #logging.debug(f"error on {self.action}({topic=}, {payload=}) : {e}. Retry without topic...")
                try:
                    return self.action(payload)
                except TypeError as e:
                    #logging.debug(f"error on {self.action}({payload=}) : {e}. Retry without payload...")
                    return self.action()
        else:
            print(f"Error : {self} has not attribute 'action'")

    def reverse_topic(self)->str:
        '''return the reverse topic name
        '''
        if type(self._reverse_topic)==str:
            return self._reverse_topic
        elif self._reverse_topic and self.read:
            return f"{self}_"
        
    def reverse_topic_action(self)->str:
        '''return the reverse topic name
        '''
        if type(self._reverse_topic)==str:
            return self.reverse_topic
        else:
            return f"{self}_"

    async def send_async(self, publisher: function):
        '''Method call by Fmpyiot to send : topic, payload = read(...)
        '''
        if self.send_period:
            await asyncio.sleep(self.send_period)
        payload = await self.get_payload_async()
        await publisher(str(self), payload)

    def attach(self, iot):
        pass

    ################
    # ASYNCIO      #
    ################


    async def get_payload_async(self, topic:str=None, payload:any=None)->any:
        ''' Read the device and return payload
        read function can accept arguments : (inital topic, initial payload), just initial payload or nothing
        '''
        if self.read:
            try:
                return await self.run_callback_async(self.read, topic, payload)
            except TypeError:
                try:
                    return await self.run_callback_async(self.read, payload)
                except TypeError:
                    return await self.run_callback_async(self.read)

    async def do_action_async(self, topic:str=None, payload:str=None)->str:
        '''Execute the action method and return (if exist) the value
        action function can accept arguments : (inital topic, initial payload), just initial payload or nothing
        '''
        # la fonction action pour prendre 2,1 ou 0 arguments
        # Et je n'ai pas trouvé comment connaitre en micropython le nombre d'arguments
        # Il existe la lib inspect, mais elle ne fonctionne pas avec les lambda function!
        # TODO : trouver une autre solution car quand il y a une TypeError dans la callback => on merde!
        #logging.debug(f"do_action_async[{self}]({topic},{payload})...")
        if self.action:
            try:
                return await self.run_callback_async(self.action, topic, payload)
            except TypeError as e:
                #logging.debug(f"error on {self.action}({topic=}, {payload=}) : {e}. Retry without topic...")
                try:
                    return await self.run_callback_async(self.action, payload)
                except TypeError as e:
                    #logging.debug(f"error on {self.action}({topic=}, {payload=}) : {e} Retry without payload...")
                    return await self.run_callback_async(self.action)
        else:
            print(f"Error : {self} has not attribute 'action'")

    async def get_a_callback(self, callback):
        '''Return a async callback
        '''
        async def callback(*_args, **_kwargs):
            return await self.run_callback_async(self, callback, *_args, **_kwargs)
        return callback
    
    async def run_callback_async(self, callback, *args, **kwargs):
        '''Execute de manière asynchone (ou pas) une callback
        '''
        #todo : never crash!
        #logging.debug(f"run_callback_async(callback={callback}, args={args}, kwargs={kwargs})")
        routine = callback(*args, **kwargs)
        if self.is_coroutine(routine):
            #logging.debug("It is a coroutine!")
            return await routine
        else:
            #logging.debug(f"It is not a coroutine. callback return value = {routine}.")
            return routine
    
    def get_routine(self, publisher):
        if self.sleep_mode:
            async def _send_topic_async():
                await self.send_async(publisher)
        else:
            async def _send_topic_async():
                while True:
                    await self.send_async(publisher)
        return _send_topic_async

    def is_coroutine(self, fn):
        return isinstance(fn, self.type_generator)

    type_generator = type((lambda: (yield))())

    ################
    # WEB      #
    ################

    
    def to_html(self)->str:
        '''renvoie un code html représantant le topic (sans valeur)
        '''
        html = ""
        if self.read:    
            html+= self.html_reader()
        if self.action:
            html+= self.html_actionner()
        return html

    def get_id(self)->str:
        return "T"+re.sub(r'\W','_',self.topic)
    
    def html_reader(self)->str:
        '''renvoie le code html pour "topic : valeur"
        '''
        return f'<div><span class = "topic">{self.topic}</span><span class="topic-sep"> = </span><span class="topic-value" id = "{self.get_id()}"></span></div>'

    def html_actionner(self)->str:
        '''Renvoie le code html d'un bouton + 2 paramètres(topic et payload)
        '''
        id = "action_"+self.get_id()
        button = f'<input class="btn btn-primary mt-2" type="submit" name="{id}" value="{id}">'
        _topic = f'<span><input type = "text" class="form_control" id = "_topic_{id}" placeholder="_topic"></span>'
        _payload = f'<span><input type = "text" class="form_control" id = "_payload_{id}" placeholder = "_payload"></span>'
        return f'<div>{button}<span>(</span>{_topic}<span>,</span>{_payload}<span>)</span></div>'
    
class TopicRead(Topic):
    '''Un topic de type read
    '''
    def __init__(self, topic:str,
                 read:function = None,
                 send_period:float = None,
                 reverse_topic:bool|str = True,
                 send_period_as_param:bool=True,
                 ):
        super().__init__(topic=topic, read=read, send_period=send_period, reverse_topic=reverse_topic, send_period_as_param=send_period_as_param)

class TopicAction(Topic):
    '''Un topic de type action
    '''
    def __init__(self, topic:str,
                 action:function = None,
                reverse_topic:bool|str = True,):
        super().__init__(topic=topic, action=action)


class TopicIrq(Topic):
    ''' Un topic basé sur l'intéruption matérielle d'un GPIO.
    En fait, on va lier une callback à lIRQ qui va juste remplir un buffer avec les valeurs de la pin 
    '''
    def __init__(self, topic:str,
                 pin:Pin | int,
                 trigger:int = None,
                 values:tuple[any]=None,
                 rate_limit:int=1, #TODO : le réutiliser
                 reverse_topic:bool = True,
                 read:function = None,
                 action:function = None,
                 buffer_size = 10):
        self.pin = pin if type(pin)==Pin else Pin(pin)
        self.trigger = trigger
        self.pin.init(Pin.IN)
        self.values = values
        self.rate_limit = rate_limit
        self.new_irq_time = time.time()
        super().__init__(topic, reverse_topic=reverse_topic, read=read, action = action)
        if self.read is None:
            self.read = self._read
        self.irq_buffer = BufferBits(buffer_size)

    def _read(self, topic:str, payload:str)->any:
        if self.values and len(self.values)==2:
            return self.values[self.pin()]
        else:
            return self.pin()

    def attach(self, iot):
        '''Lie l'intéruption au FmPtIot
        '''
        def callback(pin):
            self.irq_buffer.append(pin.value())
            logging.debug(f"irq_buffer = {self.irq_buffer}")
        self.pin.irq(callback, self.trigger)
        async def do_irq_action():
            for pin_value in self.irq_buffer:
                logging.debug(f"new IRQ event : {self.topic} = {pin_value}")
                await self.send_async(iot.publish_async)
                if self.action:
                    await self.do_action_async(self.topic, pin_value)
        iot.add_topic(TopicRoutine(action = do_irq_action,send_period=0.1))

class TopicRoutine(Topic):
    ''' Pas vraiment un Topic comme les autres : plutôt une routine qui sera executée comme tache
    '''
    def __init__(self,
                 action:function = None, send_period = None):
        super().__init__(None, action=action, send_period= send_period)
        self.none_topic_id = 0

    def get_id(self)->str:
        self.none_topic_id += 1
        return "T"+re.sub(r'\W','_',f"Routine{self.none_topic_id-1}")
    
    def is_auto_send(self) -> bool:
        return True
    
    def get_routine(self, publisher):
        '''renvoie la routine 
        '''
        if self.send_period:
            if self.sleep_mode:
                async def routine():
                    await self.do_action_async()
            else:
                async def routine():
                    while True:
                        await self.do_action_async()
                        await asyncio.sleep(self.send_period)
            return routine
        else:
            return self.do_action_async
        
    def to_html(self)->str:
        '''renvoie un code html représantant le topic (sans valeur)
        '''
        return ""

class TopicOnChange(Topic):
    '''Un topic qui sera envpyé quand la valeur change
    '''
    def __init__(self,
                 topic:str, 
                 read:function,
                 variation:float=0,
                 percent:bool=False,
                 period:float=None,
                 reverse_topic:bool = True
                 ):
        '''
        - read          :   function for reading the value args : topic, payload
        - variation     :   variation mini à partir de laquelle la valeur est renvoyé
        - percent       :   si True, variaotion est exprimée en % de la valeur précédente
        - period        :   period (s) between 2 read
        - reverse_topic :   if True : a reverse topic is créated (to force reading)
        '''
        super().__init__(topic,
                         send_period=period,
                         reverse_topic=reverse_topic,
                         read=read,
                         )
        self.last_value = None
        self.percent = percent
        self.min_variation = variation

    async def send_async(self, publisher: function):
        '''Method call by Fmpyiot to send : topic, payload = read(...)
        '''
        if self.send_period:
            await asyncio.sleep(self.send_period)
        payload = await self.get_payload_async()
        if self.is_changed(payload):
            await publisher(str(self), payload)
    
    
    def is_auto_send(self)->bool:
        return True

    def is_changed(self, payload):
        '''Check is payload change enough
        '''
        if self.last_value is None \
            or not self.percent and abs(self.last_value -payload)>=self.min_variation \
            or self.percent and abs((self.last_value - payload)/self.last_value)*100>=self.min_variation:
            self.last_value = payload
            return True