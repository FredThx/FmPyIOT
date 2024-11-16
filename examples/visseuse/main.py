'''
Un detecteur de vis longue pour bol de vis OLFA

Entrées :
    -   Capteur de proximité inductif FIT0658 (sortie NPN (NO)) 4mm
    -   Bouton de RAZ
Sorties:
    -   2 leds (verte, rouge)
    -   1 buzzer
    -   1 relais 220V 10A

Principe:
    Quand le capteur inductif détect une présence
        -   la led rouge s'allume et la vert s'éteint
        -   le buzzer s'allume
        -   le relais est activé
    Sinon, le contraire

Auteur : Fredthx pour Olfa
date : 28/10/2023
'''
from machine import Pin, Timer



proxi = Pin(17, Pin.IN)
led_red = Pin(16,Pin.OUT)
led_green = Pin(12,Pin.OUT)
relais = Pin(14,Pin.OUT)
buzzer = Pin(15, Pin.OUT)
bt_reset = Pin(13,Pin.IN)

# Par défault
led_green.on()
led_red.off()

# Callback des intéruptions
def on_pin_irq(pin):
    pin.irq(None) #Disable IRQ
    Timer(period = 10, mode=Timer.ONE_SHOT, callback=lambda tim:on_pin_change(pin))

def on_pin_change(pin):
    #print(f"{pin} is probably falling! value = {pin()}")
    if pin.value()==0:
        print(f"{pin} is falling!")
        if pin == bt_reset: # Si RAZ
            led_red.off()
            led_green.on()
            relais.off()
            buzzer.off()
        else: # Si detection
            led_red.on()
            led_green.off()
            relais.on()
            buzzer.on()
    pin.irq(on_pin_irq, Pin.IRQ_FALLING)

# Les intéruptions
proxi.irq(on_pin_irq, Pin.IRQ_FALLING)
bt_reset.irq(on_pin_irq, Pin.IRQ_FALLING)
