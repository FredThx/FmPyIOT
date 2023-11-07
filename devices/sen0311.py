
from machine import UART
import time
import uasyncio as asyncio

try:
    del len #BUG micropython!!!!
except:
    pass

class Sen0311:
    '''A ultrasonic distance sensor with UART connectivity
    DFROBOT SEN0311
    '''
    ## Board status 
    STA_OK = 0x00
    STA_ERR_CHECKSUM = 0x01
    STA_ERR_SERIAL = 0x02
    STA_ERR_CHECK_OUT_LIMIT = 0x03
    STA_ERR_CHECK_LOW_LIMIT = 0x04
    STA_ERR_DATA = 0x05

    ## last operate status, users can use this variable to determine the result of a function call. 
    last_operate_status = STA_OK

    ## variable 
    distance = 0

    ## Maximum range
    distance_max = 4500
    distance_min = 0
    range_max = 4500

    def __init__(self, uart_id:int=1, timeout:int=100):
        '''
        uart_id : 0 | 1
        timeout : ms
        '''
        self._ser = UART(uart_id, 9600)
        self._ser.init(9600, bits=8, parity=None, stop=1)
        self.timeout = timeout

    def set_dis_range(self, min, max):
        self.distance_max = max
        self.distance_min = min

    def _check_sum(self, l):
        return (l[0] + l[1] + l[2])&0x00ff

    def _measure(self):
        buf = self._ser.read()
        if buf:
            while len(buf)>4 and buf[-4]!=0xFF:
                buf = buf[:-1]
            data = buf[-4:]
            if len(data)==4 and data[0] == 0xFF:
                sum = self._check_sum(data)
                if sum != data[3]:
                    self.last_operate_status = self.STA_ERR_CHECKSUM
                else:
                    self.distance = data[1]*256 + data[2]
                    self.last_operate_status = self.STA_OK
                if self.distance > self.distance_max:
                    self.last_operate_status = self.STA_ERR_CHECK_OUT_LIMIT
                    self.distance = self.distance_max
                elif self.distance < self.distance_min:
                    self.last_operate_status = self.STA_ERR_CHECK_LOW_LIMIT
                    self.distance = self.distance_min
                return self.distance
            else:
                self.last_operate_status = self.STA_ERR_DATA
        else:
            self.last_operate_status = self.STA_ERR_SERIAL

    def get_distance(self, timeout:int=None)-> int:
        '''
        Get measured distance
        '''
        timeout = time.ticks_add(time.ticks_ms(), timeout or self.timeout)
        self.distance = None
        
        while self.distance is None and time.ticks_ms()<timeout:
            self._measure()
        return self.distance
    
    

    async def get_distance_async(self, timeout:float=1):
        '''Get distance async
        '''
        timeout = time.ticks_add(time.ticks_ms(), timeout or self.timeout)
        while self._measure() is None and time.ticks_ms()<timeout:
            asyncio.sleep_ms(10)
        return self.distance
