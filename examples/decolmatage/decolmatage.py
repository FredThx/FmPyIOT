
from machine import Pin, Timer
import time

class Decolmatage:
    '''4 relais pour piloter des electrovannes d'air comprimé
    '''
    def __init__(
            self, 
            relais:list[Pin], tempo1:float=30, tempo2:float=0.4, led = None):
        self.relais = relais
        for i, rel in enumerate(self.relais):
            if type(rel)==int:
                self.relais[i]=Pin(rel, Pin.OUT)
            else:
                rel.init(Pin.OUT)
        self.tempo1 = int(tempo1*1000) #ms
        self.tempo2 = int(tempo2*1000) #ms
        self.tim1 = Timer()
        self.tim2 = Timer()
        self.led = led
        self.led.init(Pin.OUT)
        self.tim_led = Timer()
        if self.led:
            tim_led = Timer()
            tim_led.init(
                period = 1000,
                mode = Timer.PERIODIC,
                callback = self.blink_led
            )

    def blink_led(self, tim:Timer):
        self.led.on()
        self.tim_led.init(
            period = 200,
            mode = Timer.ONE_SHOT,
            callback = lambda t:self.led.off()
        )

    
    def souffle(self, rel:Pin):
        print(f"Souffle on {rel}")
        rel.on()
        self.tim2.init(period = self.tempo2,
                 mode=Timer.ONE_SHOT,
                 callback=lambda x:rel.off())
    
    def next_souffle(self, tim:Timer):
        rel = self.relais.pop(0)
        self.souffle(rel)
        self.relais.append(rel)

    def run(self):
        self.tim1.init(period = self.tempo1,
                       mode = Timer.PERIODIC,
                       callback = self.next_souffle)
    def stop(self):
        self.tim1.deinit()

if __name__=='__main__':
    decolmate = Decolmatage([25],10,1)
    decolmate.run()