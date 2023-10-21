from machine import Pin
from decolmatage import Decolmatage


decolmate = Decolmatage(
        relais=[Pin(18),Pin(19),Pin(20),Pin(21)],
        tempo1=60,
        tempo2=0.65,
        led = Pin(25))
#decolmate = Decolmatage([Pin(25),Pin(19),Pin(25),Pin(21)],10,0.4)
decolmate.run()