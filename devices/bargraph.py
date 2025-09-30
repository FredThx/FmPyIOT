from machine import Pin, PWM


class BarGraph:
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
        assert 0 <= level <= len(self.leds), f"level doit être entre 0 et {len(self.leds)}"
        for i, led in enumerate(self.leds):
            led.value(i < level)

class BarGraphPWM(BarGraph):
    '''Les leds sous forme de bargraph avec PWM
    '''
    def __init__(self, leds: list[int|Pin], freq:int=1000):
        '''Initialise les leds du bargraph en PWM
        leds : liste de Pin ou de numéro de pin
        freq : fréquence du PWM
        '''
        self.leds = [PWM(pin if isinstance(pin,Pin) else Pin(pin, Pin.OUT), freq=freq) for pin in leds]
        self.set_level(0)

    def set_level(self, level:int, facteur:float=2.0):
        '''Allume les leds jusqu'au niveau level en PWM.
        Les leds sont atténuées en fonction de leur position
        (proche de level : maximum, loin de level : minimum)
        level : niveau de 0 à 10
        facteur : facteur d'atténuation (plus il est grand, plus la différence entre les leds est grande)
        '''
        assert 0 <= level <= len(self.leds), f"level doit être entre 0 et {len(self.leds)}"
        for i, led in enumerate(self.leds):
            if i < level:
                led.duty_u16(int(65535/((level-i)**facteur)))
            else:
                led.duty_u16(0)
