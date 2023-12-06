import time
from machine import Pin
import uasyncio as asyncio

class StepperMotor:

    def __init__(self, pins:list[Pin|int], delay:int = 1, half_step:bool = False):
        '''Init stepper motor
        pins        : list of pins in the correct order
        delay      : default delais between steps in millisecondes
        half_step   : for half step mode
        '''
        self.pins = []
        for pin in pins:
            if type(pin)==int:
                self.pins.append(Pin(pin, Pin.OUT))
            else:
                self.pins.append(pin)
                pin.init(mode = Pin.OUT)
        self.delay = delay
        if half_step:
            self.step_sequence = [
                [1,0,0,1],
                [1,0,0,0],
                [1,1,0,0],
                [0,1,0,0],
                [0,1,1,0],
                [0,0,1,0],
                [0,0,1,1],
                [0,0,0,1]]
        else:
            self.step_sequence = [
                [1,0,0,1],
                [1,1,0,0],
                [0,1,1,0],
                [0,0,1,1]]
        self.step_index = 0


    def run(self, steps:int, delay:float=None):
        ''' Do a number of steps (negative value => reverse direction)
        '''
        asyncio.run(self.run_async(steps,delay))

    async def run_async(self, steps:int, delay:int=None):
        ''' Do a number of steps (negative value => reverse direction)
        asyncio mode
        '''
        direction = 1 if steps>0 else -1
        delay = delay or self.delay
        for i in range(steps*direction):
            self.step_index = (self.step_index + direction) % len(self.step_sequence)
            for index, pin in enumerate(self.pins):
                pin.value(self.step_sequence[self.step_index][index])
            await asyncio.sleep_ms(delay)


if __name__ == "__main__":
    try:
        del len #bug!!!)
    except:
        pass
    motor = StepperMotor([10,11,12,13])
    motor.run(50)
    motor.run(-50)
