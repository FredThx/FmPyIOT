import time, logging
from machine import Pin
#from fmpyiot.fmpyiot_2 import FmPyIot

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
                 reverse_topic:bool = True,
                 read:function = None,
                 action:function = None):
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
        self._reverse_topic = reverse_topic
        self.read = read
        self.action = action
        self.last_send = 0

    def __str__(self)->str:
        return self.topic

    @never_crash
    def get_payload(self, topic:str=None, payload:any=None)->any:
        ''' Read the device and return payload
        read function can accept arguments : (inital topic, initial payload), just initial payload or nothing
        '''
        if self.read:
            try:
                return self.read(topic, payload)
            except TypeError:
                try:
                    return self.read(payload)
                except TypeError:
                    return self.read()
        else:
            print(f"Error : {self} has to attribute 'read'")


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
                return str(self.action(topic, payload))
            except TypeError as e:
                #print(e)
                try:
                    return str(self.action(payload))
                except TypeError as e:
                    #print(e)
                    return str(self.action())
        else:
            print(f"Error : {self} has not attribute 'action'")

    def reverse_topic(self)->str:
        '''return the reverse topic name
        '''
        if self._reverse_topic and self.read:
            return f"{self}_"
        
    def reverse_topic_action(self)->str:
        '''return the reverse topic name
        '''
        return f"{self}_"
    
    def auto_send(self, publisher: function):
        '''Method call by Fmpyiot every timer period
        '''
        if self.send_period and time.time()>self.last_send + self.send_period:
            publisher(self)
            self.last_send = time.time()

    async def a_auto_send(self, publisher: function):
        '''Method call by Fmpyiot every timer period
        '''
        if self.send_period and time.time()>self.last_send + self.send_period:
            await publisher(self)
            self.last_send = time.time()

    def attach(self, iot):
        pass

    ################
    # ASYNCIO      #
    ################


    async def a_get_payload(self, topic:str=None, payload:any=None)->any:
        ''' Read the device and return payload
        read function can accept arguments : (inital topic, initial payload), just initial payload or nothing
        '''
        if self.read:
            try:
                return str(await self.a_run_callback(self.read, topic, payload))
            except TypeError:
                try:
                    return str(await self.a_run_callback(self.read, payload))
                except TypeError:
                    return str(await self.a_run_callback(self.read))
        else:
            print(f"Error : {self} has to attribute 'read'")

    async def a_do_action(self, topic:str, payload:str)->str:
        '''Execute the action method and return (if exist) the value
        action function can accept arguments : (inital topic, initial payload), just initial payload or nothing
        '''
        # la fonction action pour prendre 2,1 ou 0 arguments
        # Et je n'ai pas trouvé comment connaitre en micropython le nombre d'arguments
        # Il existe la lib inspect, mais elle ne fonctionne pas avec les lambda function!
        # TODO : trouver une autre solution car quand il y a une TypeError dans la callback => on merde!
        logging.debug(f"a_do_action[{self}]({topic},{payload})...")
        if self.action:
            try:
                return await self.a_run_callback(self.action, topic, payload)
            except TypeError as e:
                print(e)
                try:
                    return str(await self.a_run_callback(self.action, payload))
                except TypeError as e:
                    print(e)
                    return str(await self.a_run_callback(self.action))
        else:
            print(f"Error : {self} has not attribute 'action'")

    async def get_a_callback(self, callback):
        '''Return a async callback
        '''
        async def callback(*_args, **_kwargs):
            return await self.a_run_callback(self, callback, *_args, **_kwargs)
        return callback
    
    async def a_run_callback(self, callback, *args, **kwargs):
        '''Execute de manière asynchone (ou pas) une callback
        '''
        #todo : never crash!
        logging.debug(f"a_run_callback(callback={callback}, args={args}, kwargs={kwargs})")
        routine = callback(*args, **kwargs)
        if self.is_coroutine(routine):
            logging.debug("It is a coroutine!")
            return await routine
        else:
            logging.debug(f"It is not a coroutine. callback return value = {routine}.")
            return routine

    def is_coroutine(self, fn):
        return isinstance(fn, self.type_generator)

    type_generator = type((lambda: (yield))())




class TopicIrq(Topic):
    ''' Un topic basé sur l'intéruption matérielle d'un GPIO
    '''
    def __init__(self, topic:str,
                 pin:Pin | int,
                 trigger:int = None,
                 values:tuple[any]=None,
                 rate_limit:int=1, 
                 reverse_topic:bool = True,
                 read:function = None,
                 action:function = None):
        self.pin = pin if type(pin)==Pin else Pin(pin)
        self.trigger = trigger
        self.pin.init(Pin.IN)
        self.values = values
        self.rate_limit = rate_limit
        self.new_irq_time = time.time()
        super().__init__(topic, reverse_topic=reverse_topic, read=read, action = action)
        if self.read is None:
            self.read = self._read

    def _read(self, topic:str, payload:str)->any:
        if self.values and len(self.values)==2:
            return self.values[self.pin()]
        else:
            return self.pin()

    def attach(self, iot):
        '''Lie l'intéruption => iot => lmqtt
        '''
        def callback(pin):
            if time.time()>self.new_irq_time:
                self.new_irq_time = time.time() + self.rate_limit
                iot.publish_topic(self)
                
        self.pin.irq(callback, self.trigger)

