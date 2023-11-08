import uio, os
import uasyncio as asyncio

try:
    del len # Super bug: len est affcté à 62???
except KeyError:
    pass

class ReplStream(uio.IOBase):
    def __init__(self, size = 100):
        self.queue:Queue = Queue(size)
        self.current_line:str = ""
        self.debug = []

    def _putc(self, c):
        '''Ajout un byte au REPL
        '''
        c = chr(c)
        if c == '\n':
            self._newline()
        else:
            self.current_line += c

    def write(self, buf):
        '''Utilisé par dupterm
        '''
        self.debug.append(len(buf))
        i = 0
        while i < len(buf):
            c = buf[i]    
            self._putc(c)
            i += 1
        return len(buf)

    def readinto(self, buf, nbytes=0):
        '''Utilisé par dupterm
        '''
        return None
        
    def _newline(self):
        '''New line 
        '''
        if self.current_line:
            self.queue.put(self.current_line)
            self.current_line = ""

        
    def exec(self, cmd:str):
        '''Execute une commande
        '''
        self._newline()
        self.queue.put(f">>>{cmd}")
        result = None
        try:
            result = eval(cmd)#toto : gerer globals et locals pour limiter
        except Exception:
            try:
                exec(cmd)#toto : gerer globals et locals pour limiter
            except Exception as e2:
                self.queue.put(str(e2))
        if result:
            self._newline()
            self.queue.put(result)
            return result
        else:
            return ""

class Queue:
    def __init__(self, size:int):
        self._queue = [0]*size
        self._size = size
        self._write_index = 0
        self._read_index = 0
        self._evt = asyncio.Event()
        self.discards = 0

    def put(self, val:str):
        self._queue[self._write_index] = val
        self._evt.set() #libère l'event
        self._write_index = (self._write_index + 1) % self._size
        if self.is_empty():
            self._read_index = (self._read_index + 1) % self._size  # Discard a value
            self.discards += 1

    def __aiter__(self):
        return self

    def is_empty(self)->bool:
        '''Queue is empty index read == index write
        '''
        return self._read_index == self._write_index

    async def __anext__(self):
        if self.is_empty():
            self._evt.clear()
            await self._evt.wait() #Attend que l'event soit libéré
        result = self._queue[self._read_index]
        self._read_index = (self._read_index + 1) % self._size
        return result
    
    def read(self):
        '''Lit la queue (renvoie None si vide)
        '''
        if not self.is_empty():
            result = self._queue[self._read_index]
            self._read_index = (self._read_index + 1) % self._size
            return result
        



class REPL():
    '''Une classe pour dupliquer le REPL avec lecture async
    '''
    def __init__(self):
        self.stream = ReplStream()
        os.dupterm(self.stream)

    def deinit(self):
        os.dupterm(None)

    @property
    def queue(self):
        return self.stream.queue

    def read(self):
        lines = []
        while line:=self.queue.read():
            lines.append(line)
        return lines

    async def exec(self, cmd:str):
        return self.stream.exec(cmd)