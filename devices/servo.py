from machine import Pin, PWM
import time
import uasyncio as asyncio


class Servo:
    '''
    Un servomoteur
    '''
    def __init__(self, pin:Pin|int, freq : int = 50, duty_min : float = 0.5, duty_max : float = 2.6
                 ):
        '''
            pin         :   (machine.Pin) Pin de commande du servomoteur
            freq        :   (int) Frequence du signal PWM
            duty_min    :   (float) Durée du signal PWM pour 0° en ms
            duty_max    :   (float) Durée du signal PWM pour 180° en ms
        '''
        self.pin = pin if isinstance(pin, Pin) else Pin(pin)
        self.pin.init(mode=Pin.OUT)
        self.freq = freq
        self.duty_min = duty_min
        self.duty_max = duty_max
        self.start()
    
    def move(self, angle:int, speed:float=1.0):
        '''Déplace le servomoteur à une position donnée
            angle   :   (int) Angle de 0 à 180°
            speed   :   (int) Vitesse de déplacement en degré par ms
        '''
        current_angle = self.angle()
        step = 1 if angle > current_angle else -1
        for a in range(current_angle, angle, step):
            self.angle(a+1)
            time.sleep_us(int(1000/speed))

    async def move_async(self, angle:int, speed:float=1.0):
        '''Déplace le servomoteur à une position donnée de manière asynchrone
        '''
        current_angle = self.angle()
        step = 1 if angle > current_angle else -1
        for a in range(current_angle, angle, step):
            self.angle(a+1)
            await asyncio.sleep_ms(int(1/speed))
            

    def angle(self, angle:int=None)->int:
        '''Set or get the angle of the servo
            angle   :   (int) Angle de 0 à 180°
        '''
        if angle is not None:
            assert angle >= 0 and angle <= 180, "angle error : must be in 0..180"
            duty = self.duty_min + (self.duty_max - self.duty_min) * angle / 180
            self.duty_ms(duty)
        #Read the real angle
        duty_ms = self.pwm.duty_u16() *1000 / (65536*self.freq)
        angle = (duty_ms - self.duty_min) * 180 // (self.duty_max - self.duty_min)
        return int(max(0,angle))

    def duty_ms(self, duty_ms:int):
        '''Définit la durée du signal PWM en ms
            duty_ms     :   (int) durée du signal en ms
        '''
        self.pwm.duty_u16(int(duty_ms*65536*self.freq/1000))

    def start(self):
        '''Initialise le PWM
        '''
        self.pwm = PWM(self.pin, self.freq)

    def stop(self):
        '''Arrête le PWM
        '''
        self.pwm.deinit()