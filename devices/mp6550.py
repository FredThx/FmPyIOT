'''MP6560 est un driver de moteur CC
avec
- pilotage de la vitesse et du sens avec deux PWM
- lecture du courant

info : https://www.pololu.com/product/4733

'''

from machine import Pin, PWM, ADC



class MP6550:
    '''Single Brushed DC Motor Driver Carrier
    '''
    def __init__(
            self, pinIN1:Pin,
            pinIN2:Pin,
            pinVISEN:Pin=None,
            pinSLEEP:Pin = None,
            pwm_frequency = 1000,
            ):
        self.pinIN1 = Pin(pinIN1) if type(pinIN1)==int else pinIN1
        self.pinIN2 = Pin(pinIN2) if type(pinIN2)==int else pinIN2
        self.pinVISEN = Pin(pinVISEN) if type(pinVISEN)==int else pinVISEN
        self.pinSLEEP = Pin(pinSLEEP) if type(pinSLEEP)==int else pinSLEEP
        self.pinIN1.init(Pin.OUT)
        self.pwmIN1 = PWM(self.pinIN1)
        self.pwmIN1.freq(pwm_frequency)
        self.pwmIN1.duty_u16(0)
        self.pinIN2.init(Pin.OUT)
        self.pwmIN2 = PWM(self.pinIN2)
        self.pwmIN2.freq(pwm_frequency)
        self.pwmIN2.duty_u16(0)
        if self.pinVISEN:
            self.adcVISEN = ADC(self.pinVISEN)
        if self.pinSLEEP:
            self.pinSLEEP.init(Pin.OUT)
        self.speed = 0.0 #float 0.0-1.0
        self.direction = 0 #int -1,0,1
    
    def set_speed(self, speed:float):
        assert 0<=speed<=1, "speed must be between 0.0 and 1.0"
        self.speed = speed
        self._apply_changes()

    def set_direction(self, direction:int):
        assert direction in [-1,0,1], "direction muste be -1, 0 or 1"
        self.direction = direction
        self._apply_changes()

    def _apply_changes(self):
        if self.direction == -1:
            self.pwmIN1.duty_u16(int(self.speed*65535))
            self.pwmIN2.duty_u16(0)
        elif self.direction == 1:
            self.pwmIN1.duty_u16(0)
            self.pwmIN2.duty_u16(int(self.speed*65535))
        else:
            self.pwmIN1.duty_u16(0)
            self.pwmIN2.duty_u16(0)
    
    def get_current(self)->float:
        '''Return the motor current en A
        '''
        return (self.adcVISEN.read_u16()*3.3 / 65535) / 0.2 # 200 mV / A
    




