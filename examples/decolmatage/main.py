from machine import Pin
from decolmatage import Decolmatage


decolmate = Decolmatage([Pin(18),Pin(19),Pin(20),Pin(21)],60,0.4)
#decolmate = Decolmatage([Pin(25),Pin(19),Pin(25),Pin(21)],10,0.4)
decolmate.run()