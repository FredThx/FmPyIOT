import time

class Tempo:

    def __init__(self, temporisation:float, debug = False):
        '''temporisation : seconds
        '''
        self.temporisation = temporisation
        self.tempo_ns = 0
        self.debug = debug

    def set(self, level:int):
        '''Set the input level (0|1)
        '''
        if self.debug:
            print(f"Tempo : set {level}")
        if level: #HIGH
            self.tempo_ns = -1
        else: #LOW
            if self.tempo_ns == -1:
                self.tempo_ns = time.time_ns() + int(self.temporisation * 1000_000_000.0)

    def read(self):
        '''Read the output
        '''
        return self.tempo_ns == -1 or time.time_ns() < self.tempo_ns

if __name__ == "__main__":
    from machine import Pin
    detecteur = Pin(15, Pin.ALT)
    tempo = Tempo(2)
    detecteur.irq(
        handler = lambda pin:tempo.set(not pin.value()),
        trigger =  Pin.IRQ_FALLING | Pin.IRQ_RISING
        )
    while True:
        if tempo.read():
            print("HIGHT")
        else:
            print("LOW")
        time.sleep_ms(50)