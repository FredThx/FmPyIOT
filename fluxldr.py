import machine



class LuxLDR:
    '''Une photorésistance.
    
    --------- Vcc
    |
[Photoresistance]
    |
    ---------- ADC0 | ADC1 | ADC2
    |
   [R]
    |
    ---------- 0V

    '''
    def __init__(self, channel:int = None, pin : machine.Pin | int = None, R = 10_000, R0 = 1_000_000, k = 1):
        '''
        channel     :   0,1,2 for ADC0, ADC1, ADC2
        pin         :   int or Pin : 26 : ADC0, 27 : ADC1, 28 : ADC2
        R           :   Resistor R
        R0          :   Photoresitor resistance maxi (default : 1_000_000 1MR)
        k           :   k factor of the ldr (default = 1)
        '''
        if pin and type(pin)==int:
            pin = machine.Pin(pin)
        self.analog_pin = machine.ADC(pin if channel is None else channel)
        self.R = R
        self.R0 = R0
        self.k = k

    def read(self)-> float:
        '''return a float between 0-1
        '''
        R_ldr = self.R*(65535/self.analog_pin.read_u16() - 1)
        return  self.R0/R_ldr/self.k