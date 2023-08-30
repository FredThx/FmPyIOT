
from machine import Pin
from devices.mp6550 import MP6550
import time
from tempo import Tempo


class Enrouleur:

    def __init__(
            self, moteur:MP6550,
            detecteur:Pin,
            temporisation:float,
            pin_forward:Pin=None,
            pin_backward:Pin = None,
            pin_force_forward:Pin=None,
            pin_force_backward:Pin=None ):
        self.moteur = moteur
        self.detecteur = detecteur
        self.tempo = Tempo(temporisation)
        self.irq = detecteur.irq(
            handler = lambda pin:self.tempo.set(not pin.value()),
            trigger =  Pin.IRQ_FALLING | Pin.IRQ_RISING
            )
        self.pin_forward = pin_forward
        self.pin_backward = pin_backward
        self.pin_force_forward = pin_force_forward
        self.pin_force_backward = pin_force_backward

    def enroule(self):
        if self.pin_forward.value()==0:
            self.moteur.set_direction(1)
        elif self.pin_backward.value()==0:
            self.moteur.set_direction(-1)
        else:
            self.moteur.set_direction(0)

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
