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
date : 28/10/203
'''
from machine import Pin

#Les entrées
proxi = Pin(17, Pin.IN, pull=Pin.PULL_UP)
bt_reset = Pin(13,Pin.IN)

#Les sorties
led_red = Pin(16,Pin.OUT)
led_green = Pin(12,Pin.OUT)
relais = Pin(14,Pin.OUT)
buzzer = Pin(15, Pin.OUT)

# Par défault
led_green.on()
led_red.off()

# Callback des intéruptions
def on_pin_change(pin):
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
# Les intéruptions
proxi.irq(
    on_pin_change,
    Pin.IRQ_FALLING
    )

bt_reset.irq(
    on_pin_change,
    Pin.IRQ_FALLING
    )
