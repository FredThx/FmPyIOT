from machine import Pin
from onewire import OneWire
import time, ds18x20



class DS18b20:
    ''' Un ou des capteur(s) de température ds18x20 sur un bus onewire
    '''
    def __init__(self, pin:Pin|int = None, ow:OneWire = None, rom: bytearray = None):
        '''
        pin     :   machine.Pin object or int where is connected a ow bus
        ow      :   onewire.OneWire object
        rom     :   bytearray (address of the device)
        '''
        if ow:
            self.ow = ow
        elif pin:
            if type(pin)==int:
                pin = Pin(pin)
            self.ow = OneWire(pin)
        self.rom = rom
        #Scan du bus
        print(f"Scan OneWire on {self.ow.pin}")
        roms = self.ow.scan()
        if roms:
            print(f"OneWire works fine! Found {len(roms)} devices : ")
            for rom in roms:
                print(self.bytearray_to_str(rom) + (" (selected)" if rom == self.rom else ""))
        else:
            print("No device found on ow")
        self.ds = ds18x20.DS18X20(self.ow)
    
    @staticmethod
    def bytearray_to_str(rom:bytearray):
        return ",".join(hex(b) for b in rom)

    def read(self, rom:bytearray = None, delais:int = 750)-> float:
        '''
        rom (optional)  :   device address
        delais          :   delais for reading devices (ms)
        '''
        rom = rom or self.rom
        if not rom:
            roms = self.ds.scan()
            if len(roms)==1:
                rom = roms[0]
        if rom is not None:
            self.ds.convert_temp()
            time.sleep_ms(delais)
            try:
                temp = self.ds.read_temp(rom)
            except Exception as e:
                print(f"Error during temperature reading : {e}")
            else:
                return temp if temp!=85 else None
        else:
            print(f"Error reading {self} : {len(roms)} devices found.")
    
    def read_all(self)->dict:
        self.ds.convert_temp()
        time.sleep_ms(750)
        return {self.bytearray_to_str(rom) : self.ds.read_temp(rom) for rom in self.ds.scan()}

