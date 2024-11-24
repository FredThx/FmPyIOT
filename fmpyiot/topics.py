TYPE_CHECKING=False
import time, logging, re
from machine import Pin
import uasyncio as asyncio
from fmpyiot.buffer import BufferBits
if TYPE_CHECKING:
    from fmpyiot.fmpyiot import FmPyIot


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
                 action:function = None, #for compatibility old iot,
                 on_incoming:function = None,
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
        self.on_incoming = on_incoming or action # or action = for compatibility old iot,
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

    async def send_async(self, publisher: function, payload=None):
        '''Method call by Fmpyiot to send : topic, payload = read(...)
        '''
        if self.send_period:
            await asyncio.sleep(self.send_period)
        if payload is None:
            payload = await self.get_payload_async()
        await publisher(str(self), payload)

    def attach(self, iot:FmPyIot):
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

    async def do_action_async(self, topic:str=None, payload:str=None, action:function=None)->str:
        '''Execute the action method and return (if exist) the value
        action function can accept arguments : (inital topic, initial payload), just initial payload or nothing
        action (optionnal) : default : self.on_incoming
        '''
        # la fonction action pour prendre 2,1 ou 0 arguments
        # Et je n'ai pas trouvé comment connaitre en micropython le nombre d'arguments
        # Il existe la lib inspect, mais elle ne fonctionne pas avec les lambda function!
        # TODO : trouver une autre solution car quand il y a une TypeError dans la callback => on merde!
        #logging.debug(f"do_action_async[{self}]({topic},{payload})...")
        action = action or self.on_incoming
        if action:
            try:
                return await self.run_callback_async(action, topic, payload)
            except TypeError as e:
                #logging.debug(f"error on {action}({topic=}, {payload=}) : {e}. Retry without topic...")
                try:
                    return await self.run_callback_async(action, payload)
                except TypeError as e:
                    #logging.debug(f"error on {action}({topic=}, {payload=}) : {e} Retry without payload...")
                    return await self.run_callback_async(action)
        else:
            logging.error(f"Error : {self} has not attribute 'on_incoming'")

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
        if self.on_incoming:
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
                 on_incoming:function = None,
                 action:function = None, # for compatibility
                 ):
        super().__init__(topic=topic, on_incoming=on_incoming or action)


class TopicIrq(Topic):
    ''' Un topic basé sur l'intéruption matérielle d'un GPIO.
    En fait, on va lier une callback à l'IRQ qui va juste remplir un buffer avec les valeurs de la pin.
    Ensuite une routine est créé pour lire ce buffer en asyncio.
        trigger : Pin.IRQ_FALLING | Pin.IRQ_RISING | Pin.IRQ_LOW_LEVEL | Pin.IRQ_HIGH_LEVEL
        values  : None or a tuple od 2 values ("on_off", "on_on") => theses values will be send instead
        rate_limit : (s)
        buffer_size : size of the buffer used to store events (10 must be enought)
        on_irq : function called on irq event
    '''
    def __init__(self, topic:str,
                 pin:Pin | int,
                 trigger:int,
                 on_irq:function = None,
                 values:tuple[any]=None, 
                 tempo_rising:float=0, #s
                 reverse_topic:bool = True,
                 read:function = None,
                 on_incoming:function = None,
                 action:function = None, # for compatibility
                 buffer_size = 10):
        self.pin = pin if type(pin)==Pin else Pin(pin)
        self.trigger = trigger
        self.pin.init(Pin.IN)
        self.values = values
        self.on_irq = on_irq
        self.tempo_rising = int(tempo_rising * 1000) # ms
        self.idle = False
        self.new_irq_time = time.ticks_ms()
        self.irq_buffer = BufferBits(buffer_size)
        super().__init__(topic, reverse_topic=reverse_topic, read=read, on_incoming = on_incoming or action)
        if self.read is None:
            self.read = self._read

    def _read(self, topic:str, payload:str)->any:
        if self.values and len(self.values)==2:
            return self.values[self.pin()]
        else:
            return self.pin()

    def attach(self, iot:FmPyIot):
        '''Lie l'intéruption au FmPtIot
        '''
        # IRQ => buffer
        def callback(pin):
            self.irq_buffer.append(pin.value())
            print(self.irq_buffer)
        self.pin.irq(callback, self.trigger)
        # buffer => publish + action
        async def do_irq_action():
            unidle = False
            if self.tempo_rising and self.idle and self.pin.value()==0 and time.ticks_diff(time.ticks_ms(), self.new_irq_time) > 0:
                logging.info(f"RAZ idle and put new 0 on buffer")
                self.irq_buffer.append(0)
                self.idle = False
                unidle = True
            for pin_value in self.irq_buffer:
                logging.info(f"new IRQ event : {self.topic} = {pin_value}")
                if self.tempo_rising and not unidle:
                    logging.info(f"Put TopicIRQ on IDLE mode for {self.tempo_rising/1000} secondes")
                    self.new_irq_time = time.ticks_add(time.ticks_ms(), self.tempo_rising)
                    if pin_value == 0:
                        self.idle = True
                if not self.idle:
                    await self.send_async(iot.publish_async, pin_value)
                    if self.on_irq:
                        await self.do_action_async(self.topic, pin_value, action=self.on_irq)
                else:
                    logging.info(f"{self} on Idle mode. Reste {time.ticks_diff(time.ticks_ms(), self.new_irq_time)/1000} secondes.")
                asyncio.sleep(0.1)
        iot.add_topic(TopicRoutine(action = do_irq_action, send_period=0.01, send_period_as_param=False))

class TopicRoutine(Topic):
    ''' Pas vraiment un Topic comme les autres : plutôt une routine qui sera executée comme tache
        send_period     :   None : never | 0 : always, as fast as possible | x : every x secondes
    '''
    def __init__(self,
                 action:function = None, send_period = 0, send_period_as_param = True):
        self.action = action
        super().__init__(None, send_period= send_period, send_period_as_param=send_period_as_param)
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
                    await self.do_action_async(action=self.action)
            else:
                async def routine():
                    while True:
                        await self.do_action_async(action=self.action)
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
    #TODO : ajouter une callback on_change
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