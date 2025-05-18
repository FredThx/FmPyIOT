from devices.motor_stepper import StepperMotor
import json, logging

class Vanne(object):
    """
    Class representing a valve in a hydraulic system.
    """

    def __init__(self, motor:StepperMotor, json_file:str = "vanne.json", max_position:int = 1000, step = 100):
        self.motor = motor
        self.json_file = json_file
        self.max_position = max_position
        self.step = step
        self.position = self.load_position()

    async def open(self):
        '''Open the valve. ie position = 0'''
        logging.info(f"Opening valve from position {self.position} to 0")
        while self.position > 0:
            step = min(self.step, self.position)
            await self.motor.run_async(-step)
            self.set_position(self.position - step)
            self.motor.stop()

    async def close(self):
        '''Close the valve. ie position = max_position'''
        logging.info(f"Closing valve fromp position {self.position} to {self.max_position}")
        while self.position < self.max_position:
            step = min(self.step, self.max_position - self.position)
            await self.motor.run_async(step)
            self.set_position(self.position + step)
            self.motor.stop()
        
    async def move(self, steps:int):
        '''Move the valve a number of steps (negative value => reverse direction)'''
        await self.motor.run_async(steps)
        self.motor.stop()

    def init(self):
        """
        Initialize the valve (position open = 0)
        """
        self.position = 0

    def load_position(self):
        """
        Load the position of the valve from a JSON file.
        """
        try:
            with open(self.json_file, "r") as f:
                data = json.load(f)
                self.position = data.get("position", 0)
        except OSError:
            self.position = 0
        return self.position

    def set_position(self, position:int):
        """
        Save the position of the valve to a JSON file.
        """
        logging.debug(f"Saving position {position} to {self.json_file}")
        self.position = position
        with open(self.json_file, "w") as f:
            json.dump({"position": position}, f)