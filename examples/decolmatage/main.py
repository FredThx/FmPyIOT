from machine import Pin
from decolmatage import Decolmatage


decolmate = Decolmatage(
        relais=[Pin(18),Pin(19),Pin(20),Pin(21)],
        tempo1=45.0,
        tempo2=1.0,
        led = Pin(25))
decolmate.run()