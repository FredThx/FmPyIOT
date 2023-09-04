
from machine import Pin
from devices.mp6550 import MP6550
import time
from tempo import Tempo


class Enrouleur:
    '''un enrouleur pour imprimante Epson P9000
    '''
    def __init__(
            self, moteur:MP6550,
            detecteur:Pin,
            temporisation:float,
            pin_forward:Pin=None,
            pin_backward:Pin = None,
            pin_force_forward:Pin=None,
            pin_force_backward:Pin=None,
            max_current = None,
            debug = False ):
        self.moteur = moteur
        self.detecteur = detecteur
        self.tempo = Tempo(temporisation, debug=debug)
        self.irq = detecteur.irq(
            handler = lambda pin:self.tempo.set(not pin.value()),
            trigger =  Pin.IRQ_FALLING | Pin.IRQ_RISING
            )
        self.tempo.set(not self.detecteur.value())
        self.pin_forward = pin_forward
        self.pin_backward = pin_backward
        self.pin_force_forward = pin_force_forward
        self.pin_force_backward = pin_force_backward
        self.max_current = max_current
        self.debug = debug

    def enroule(self):
        if self.max_current == None or self.moteur.get_current() < self.max_current:
            if self.pin_forward.value()==0:
                self.moteur.set_direction(1)
            elif self.pin_backward.value()==0:
                self.moteur.set_direction(-1)
            else:        
                self.moteur.set_direction(0)
        else:
            self.moteur.set_direction(0)
            self.tempo.reset()
            print('MAX CURRENT!!')
                

    def run(self):
        while True:
            if self.pin_force_forward.value()==0:
                self.moteur.set_direction(1)
            elif self.pin_force_backward.value()==0:
                self.moteur.set_direction(-1)
            elif self.tempo.read():
                self.enroule()
            else:
                self.moteur.set_direction(0)
            time.sleep_ms(50)
            if self.debug and self.moteur.direction!=0:
                print(f"Direction : {self.moteur.direction}. Vitesse : {int(self.moteur.speed*100)}%. Intensité moteur : {int(self.moteur.get_current()*1000)}mA")
