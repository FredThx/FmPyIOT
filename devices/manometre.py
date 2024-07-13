from machine import Pin, ADC

class ManoAnalog:
    '''Un manomètre avec lecture Analogique
    '''
    def __init__(self, pin_adc:Pin=None,
                 max_psi:float = None, max_bars:float = None,
                 max_voltage:float=3.3, min_voltage:float=0, max_resol:int=65535,
                 no_negative:bool = False) -> None:
        '''
        pin_adc         :   adc Pin ex(GPIO28)
        max_psi         :   maximum pressure in PSI
        max_bars        :   maximum pressure in Bars
        max_voltage     :   voltage for maximum pressure
        min_voltage     :   voltage for pressure = 0
        '''
        assert max_resol>0, "max_resol must be a positif number"
        assert min_voltage < max_voltage, "min_voltage must be less than max_voltage"
        self.adc = ADC(pin_adc)
        max_bars = max_bars or max_psi / 14.504
        self.coef = max_bars/max_resol*max_voltage/(max_voltage-min_voltage)
        self.offset = - max_bars*min_voltage/(max_voltage - min_voltage)
        self.no_negative = no_negative

    def read(self, precision:int=2):
        '''Return pressure in Bars
        '''
        pressure =  round(self.adc.read_u16()*self.coef + self.offset, precision)
        if self.no_negative:
            return max(0,pressure)
        else:
            return pressure

