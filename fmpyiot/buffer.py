


class BufferBits:
    '''Un buffer de bits mutable'''
    def __init__(self, size:int):
        self.size = size
        self.buf = bytearray(size)
        self.pos = 0 # position du prochain
        self.len = 0 # nb de données sans le buffer
    
    def __repr__(self) -> str:
        _len = self.len
        repr =  f"[{','.join(map(str,self))}]"
        self.len = _len
        return repr

    def __iter__(self):
        return self._iterator()

    def _iterator(self):
        '''Drain iterator 
        '''
        while (value :=self.get()) is not None:
            yield value

    def append(self, value:int):
        self.buf[self.pos]= 1 if value else 0xff
        self.pos = (self.pos + 1)%self.size
        self.len = min(self.len+1, self.size)
        
    def get(self)->int:
        if self.len >0:
            val = 1 if self.buf[self.pos-self.len]!=0xff else 0
            self.len -=1
            return val
