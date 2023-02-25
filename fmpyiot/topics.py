import time


class Topic:
    '''Topic (Device) on a FmPyIOT object
    '''
    def __init__(self, topic:str, send_period = None, reverse_topic = True, **kwargs: function):
        '''Initialisation
        Arguments : 
            - topic (car start with ./ for relative topic name)
            - send_period : period (seconds) for auto send timer
            - functions overloaded (ex : read=lambda : 42)
                - read
        '''
        self.topic = topic
        self.send_period = send_period
        self._reverse_topic = reverse_topic
        for method, func in kwargs.items():
            setattr(self,method,func)
        self.last_send = 0

    def __str__(self):
        return self.topic

    read = None
    action = None
    #def read(self, init_topic:str=None, init_payload:str=None)->str:
    #    '''Must be overloaded
    #    topic, payload (optional)
    #    '''
    #    raise Exception("read function must be overloaded!")
    
    def get_payload(self, topic:str=None, payload:any=None):
        ''' Read the device and return payload
        read function can accept arguments : (inital topic, initial payload), just initial payload or nothing
        '''
        try:
            return self.read(topic, payload)
        except TypeError:
            try:
                return self.read(payload)
            except TypeError:
                return self.read()
            
    def do_action(self, topic:str=None, payload:str=None):
        '''Execute the action method and return (if exist) the value
        action function can accept arguments : (inital topic, initial payload), just initial payload or nothing
        '''
        try:
            return str(self.action(topic, payload))
        except TypeError:
            try:
                return str(self.action(payload))
            except TypeError:
                return str(self.action())

    def reverse_topic(self):
        '''return the server topic name
        '''
        if self._reverse_topic:
            return f"{self}_"
    
    def auto_send(self, publisher: function):
        '''Method call by Fmpyiot every timer period
        '''
        if self.send_period and time.time()>self.last_send + self.send_period:
            publisher(self)
            self.last_send = time.time()

    
