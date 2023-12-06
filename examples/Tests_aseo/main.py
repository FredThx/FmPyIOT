from devices.motor_stepper import StepperMotor
from machine import Pin

motor = StepperMotor([10,11,12,13])

bts = {
    -1 : Pin(17, Pin.IN, pull = Pin.PULL_UP), #Backward
    1 : Pin(16, Pin.IN, pull = Pin.PULL_UP) # Forward
}


while True:
    for direction, pin in bts.items():
        if pin.value() == 0:
            motor.run(direction)