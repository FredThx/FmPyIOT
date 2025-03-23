from machine import Pin


class BareGraph:
    '''Les leds sous forme de bargraph
    '''
    def __init__(self, leds: list[int|Pin]):
        '''Initialise les leds du bargraph
        leds : liste de Pin ou de numéro de pin
        '''
        self.leds = [pin if isinstance(pin,Pin) else Pin(pin, Pin.OUT) for pin in leds]
        self.set_level(0)

    def set_level(self, level:int):
        '''Allume les leds jusqu'au niveau level
        level : niveau de 0 à 10
        '''
        assert 0 <= level <= len(self.leds), f"level doit être entre 0 et {self.leds}"
        for i, led in enumerate(self.leds):
            led.value(i < level)