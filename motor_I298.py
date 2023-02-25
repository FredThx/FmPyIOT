from machine import Pin, PWM



class MotorI298:
    '''Un module pont en H pour piloter un moteur CC
    '''
    def __init__(self, pinA : Pin , pinB : Pin, pin_ena : Pin = None, freq : int = 100, duty : float = 1.0):
        '''
            pinA    :   (machine.Pin) Entrée de commande du sens du pont
            pinB    :   (machine.Pin) Entrée de commande du sens du pont
            pin_ena :   (machine.Pin) Entrée de commande Marche / Arret du pont
            freq    :   frequence du signal PWM
            duty    :   durée HIGH du signal => puissance du moteur de 0 à 1
        '''
        self.pinA = pinA
        self.pinA.init(mode=Pin.OUT)
        self.pinA.low()
        self.pinB = pinB
        self.pinB.init(mode=Pin.OUT)
        self.pinB.low()
        self.pin_ena = pin_ena
        self.pin_ena.init(mode=Pin.OUT)
        self.pin_ena.low()
        self.duty = duty
        self.freq = freq
        self.pwm = None

    def stop(self):
        if self.pin_ena:
            if self.pwm:
                self.pwm.deinit()
            self.pin_ena.init(mode=Pin.OUT)
            self.pin_ena.low()
        else:
            self.pinA.low()
            self.pinB.low()

    def run(self, reverse : bool = False, duty : float = None, freq = None):
        if reverse:
            self.pinB.low()
            self.pinA.high()
        else:
            self.pinA.low()
            self.pinB.high()
        if freq:
            self.freq = freq
        if duty:
            self.duty = duty
        assert self.duty >= 0 and self.duty<=1,"duty error : must be in 0..1"
        if self.pin_ena:
            if duty == 1.0:
                if self.pwm:
                    self.pwm.deinit()
                self.pin_ena.init(mode=Pin.OUT)
                self.pin_ena.high()
            else:
                self.pwm = PWM(self.pin_ena)
                self.pwm.freq(self.freq)
                self.pwm.duty_u16(int(self.duty*65536))
