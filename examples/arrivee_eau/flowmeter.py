from machine import Pin, Timer
import json

class FlowMeter:
    '''
    A simple flow meter class that counts impulses from a flow sensor connected to a specified pin.
    '''
    def __init__(self, pin:int, A:float, B:float, interval:int=5, auto_save:bool=False, json_file:str="flowmeter.json"):
        '''
        Initialize the flow meter with a specific pin and calibration factors.
        :param pin: The GPIO pin number where the flow sensor is connected.
        :param A: Calibration factor A for flow rate calculation.
        :param B: Calibration factor B for flow rate calculation.
            Frequency (Hz) F = A * Flow Rate (L/min) + B
        :param interval: The interval in seconds for updating the flow rate.
        :param auto_save: Whether to automatically save flow data to the JSON file.
        :param json_file: The name of the JSON file to save flow data.
        '''
        self.A=A
        self.B=B
        self.interval=interval
        self.auto_save=auto_save
        self.json_file=json_file
        self.pin = Pin(pin, Pin.IN)#, Pin.PULL_UP)
        self.pin.irq(trigger=Pin.IRQ_FALLING, handler=self._pulse_handler)
        self.pulse_count:int = 0
        self.liter_count:float = 0.0
        self.flow_rate:float=0.0
        if self.auto_save:
            self._load_from_json()
        self.timer = Timer()
        self.timer.init(period = 1000 * self.interval, mode=Timer.PERIODIC, callback=lambda t: self._calc_flow_rate())

    def _pulse_handler(self, pin):
        '''IRQ handler for counting pulses from the flow sensor.
        '''
        self.pulse_count += 1

    def _calc_flow_rate(self):
        '''Timer handler to calculate flow rate and liter count.
        '''
        pulse_count = self.pulse_count  # Capture the current pulse count
        self.pulse_count = 0  # Reset pulse count for the next interval
        volume = max((pulse_count - self.B*self.interval) / (60*self.A), 0) # litres
        self.liter_count += volume
        self.flow_rate = volume / self.interval * 60 # L/min
        if self.auto_save:
            self._save_to_json()

    def _save_to_json(self):
        '''Save the current liter_count to a JSON file.
        '''
        data = {
            "liter_count": self.liter_count
        }
        with open(self.json_file, 'w') as f:
            json.dump(data, f)

    def _load_from_json(self):
        '''Load the liter_count from a JSON file.
        '''
        try:
            with open(self.json_file, 'r') as f:
                data = json.load(f)
                self.liter_count = data.get("liter_count", 0.0)
        except (OSError, ValueError):
            self.liter_count = 0.0

    def get_flow_rate(self):
        '''
        Get the flow rate based on the pulse count and calibration factors.
        :return: The flow rate in liters per minute.
        '''
        return self.flow_rate

    def get_liter_count(self):
        '''
        Get the liter count based on the pulse count and calibration factors.
        :return: The liter count.
        '''
        return self.liter_count

    def read(self):
        '''
        Get the current flow rate and liter count.
        :return: A tuple containing the flow rate (L/min) and liter count.
        '''
        return self.get_flow_rate(), self.get_liter_count()
    
    def reset(self, volume:float=0.0):
        self.liter_count = volume