from machine import Pin
import time, logging
import uasyncio as asyncio

class PorteGarage:
    '''Une porte de garage composé de deux capteurs (porte ouverte, porte fermée) et d'un bouton poussoir
    '''
    def __init__(self,
            sensor_close : Pin,
            sensor_open : Pin,
            gate_motor_push : Pin,
            push_duration:float = 1.0):
        self.push_duration = push_duration
        self.sensor_close = sensor_close
        self.sensor_close.init(mode = Pin.IN)
        self.sensor_open = sensor_open
        self.sensor_open.init(mode = Pin.IN)
        self.gate_motor_push = gate_motor_push
        self.gate_motor_push.init(mode = Pin.OUT)
        self.gate_motor_push.off()
        self.gate_state = None

    def set_push_duration(self, value:float):
        self.push_duration = value

    def get_gate_state(self):
        if self.sensor_close.value()==0:
            if self.sensor_open.value()==0:
                self.gate_state = "ERROR" # Les deux capteurs actifs : impossible
            else:
                self.gate_state = "CLOSE"
        else:
            if self.sensor_open.value()==0:
                self.gate_state = "OPEN"
            else: # Aucun capteur actif : inconnu
                if self.gate_state == "CLOSE":
                    self.gate_state = "OPENING"
                elif self.gate_state == 'OPEN':
                    self.gate_state = "CLOSING"
        return self.gate_state

    def push_button(self):
        self.gate_motor_push.on()
        time.sleep(self.push_duration)
        self.gate_motor_push.off()
    
    async def push_button_async(self):
        self.gate_motor_push.on()
        logging.info("Porte garage : bouton poussoir ON")
        await asyncio.sleep(self.push_duration)
        self.gate_motor_push.off()
        logging.info("Porte garage : bouton poussoir OFF")