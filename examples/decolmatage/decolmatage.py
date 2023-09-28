
from machine import Pin, Timer
import time

class Decolmatage:
    '''4 relmais pour piloter des electrovannes d'air comprimé
    '''
    def __init__(
            self, 
            relais:list[Pin], tempo1:float=30, tempo2:float=0.4):
        self.relais = relais
        self.tempo1 = int(tempo1) #second
        self.tempo2 = int(tempo2 * 1000) #ms
        for i, rel in enumerate(self.relais):
            if type(rel)==int:
                self.relais[i]=Pin(rel, Pin.OUT)
            else:
                rel.init(Pin.OUT)
    
    def souffle(self, rel:Pin):
        print(f"Souffle on {rel}")
        rel.on()
        tim = Timer()
        tim.init(period = self.tempo2,
                 mode=Timer.ONE_SHOT,
                 callback=lambda x:rel.off())

    def run(self):
        while True:
            for rel in self.relais:
                self.souffle(rel)
                time.sleep(self.tempo1)

if __name__=='__main__':
    decolmate = Decolmatage([25],10,1)
    decolmate.run()