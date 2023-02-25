import dht
from machine import Pin


class DHT:
    def __init__(self, pin : Pin | int):
        if type(pin)==int:
            pin = Pin(pin)
        self.pin = pin
    
    def read(self) -> dict:
        try:
            self.device.measure()
        except Exception as e:
            print(f"Error on read DHT device {self}: {e}")
        return {
            'temperature' : self.device.temperature(),
            'humidity' : self.device.humidity(),
            }

    def read_temperature(self):
        return self.read()['temperature']

    def read_humidity(self):
        return self.read()['humidity']

class DHT11(DHT):
    def __init__(self, pin : Pin | int):
        super().__init__(pin)
        self.device = dht.DHT11(self.pin)

class DHT22(DHT):
    def __init__(self, pin : Pin | int):
        super().__init__(pin)
        self.device = dht.DHT22(self.pin)


