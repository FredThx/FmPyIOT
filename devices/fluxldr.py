import machine



class LuxLDR:
    '''Une photorésistance.
    
    --------- Vcc
    |
[Photoresistance]
    |
   [Rp]
    |
    ---------- ADC0 | ADC1 | ADC2
    |
   [R]
    |
    ---------- 0V

    '''
    def __init__(self, channel:int = None, pin : machine.Pin | int = None, R = 10_000, R0 = 1_000_000, k = 1, Rp=0, vcc=3.3, adc_ref = 3.3, resol = 16):
        '''
        channel     :   0,1,2 for ADC0, ADC1, ADC2
        pin         :   int or Pin : 26 : ADC0, 27 : ADC1, 28 : ADC2
        R           :   Resistor R
        R0          :   Photoresitor resistance maxi (default : 1_000_000 1MR)
        Rp          :   Fixed resistor (default : 0)
        k           :   k factor of the ldr (default = 1)
        vcc         :   Vcc (V) default : 3.3 V
        adc_ref     :   reference for adv (default : 3.3 V)
        resol       :   n bits (default : 16)
        '''
        if pin and type(pin)==int:
            pin = machine.Pin(pin)
        self.analog_pin = machine.ADC(pin if channel is None else channel)
        self.R = R
        self.R0 = R0
        self.k = k
        self.Rp = Rp
        self.vcc = vcc
        self.adc_ref = adc_ref
        self.resol = 2**resol-1

    def read(self)-> float:
        '''return the luminosity (Lumen)
        '''
        u = self.analog_pin.read_u16()/self.resol*self.adc_ref
        R_ldr = (self.R*self.vcc - (self.Rp+self.R))/u
        try:
            return  self.R0/R_ldr/self.k
        except ZeroDivisionError:
            return None