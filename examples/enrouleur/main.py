from machine import Pin
from devices.mp6550 import MP6550
from enrouleur import Enrouleur

moteur = MP6550(
    pinIN1=17,
    pinIN2=16,
    pinVISEN=26,
    auto_brake=True)

moteur.set_speed(1)

detecteur = Pin(15, Pin.ALT)
pin_forward = Pin(13, Pin.IN, Pin.PULL_UP)
pin_backward = Pin(14, Pin.IN, Pin.PULL_UP)
pin_force_forward = Pin(11, Pin.IN, Pin.PULL_UP)
pin_force_backward = Pin(12, Pin.IN, Pin.PULL_UP)

pin_led = Pin(10, Pin.OUT)

enrouleur = Enrouleur(
    moteur = moteur,
    detecteur=detecteur, temporisation = 5,
    pin_forward=pin_forward,
    pin_backward=pin_backward,
    pin_force_forward=pin_force_forward,
    pin_force_backward=pin_force_backward,
    pin_led = pin_led,
    max_current=0.225, # A
    debug=True)

enrouleur.run()