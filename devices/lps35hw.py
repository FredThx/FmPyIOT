import logging

class LPS35HW:
    '''LPS35HW Pressure Sensor Class.'''

    PRESS_OUT_H = 0x2A
    PRESS_OUT_L = 0x29
    PRESS_OUT_XL = 0x28
    TEMP_OUT_L = 0x2B
    TEMP_OUT_H = 0x2C
    FIFO_CTRL = 0x14
    CTRL_REG1 = 0x10
    CTRL_REG2 = 0x11

    def __init__(self, i2c, address=0x5D):
        self.i2c = i2c
        self.address = address

    def write_register(self, reg:int, data:int)-> None:
        """Write a byte to a register."""
        self.i2c.writeto_mem(self.address, reg, bytes([data]))
    
    def read_register(self, reg:int, length:int=1)->bytearray:
        """Read  bytes from a register."""
        return bytearray(self.i2c.readfrom_mem(self.address, reg, length))

    @property
    def pressure(self)->float:
        '''Read pressure in hPa from the sensor.'''
        try:
            self.write_register(self.CTRL_REG2, 0x11)  # Enable the sensor
        except OSError as e:
            logging.error(f"LPS35HW sensor not found : {e}")
        else:
            press_xl, press_l, press_h = self.read_register(self.PRESS_OUT_XL, 3)  # Read pressure data
            pressure_lbs = press_h * 256 * 256 + press_l * 256 + press_xl
            if pressure_lbs <  16777215:
                return pressure_lbs / 4096

    @property
    def temperature(self)->float:
        '''Read temperature in Celsius from the sensor.'''
        try:
            self.write_register(self.CTRL_REG2, 0x11)  # Enable the sensor
        except OSError as e:
            logging.error(f"LPS35HW sensor not found : {e}")
        else:
            temp_l, temp_h = self.read_register(self.TEMP_OUT_L, 2)  # Read pressure data
            if temp_h <  255:
                return (temp_h * 256 + temp_l) / 100