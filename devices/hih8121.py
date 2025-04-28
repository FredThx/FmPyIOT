
# Un capteur d'humidité et de température HIH8121
#    de Honeywell
#
# Auteur : Fredthx
# Date : 2023-10-01
# Version : 0.1



class HIH8121:
    ''' Un capteur d'humidité et de température HIH8121
        de Honeywell
    '''
    def __init__(self, i2c, address=0x27):
        self.i2c = i2c
        self.address = address
        self.humidity = 0.0
        self.temperature = 0.0
        self.read()


    def read(self):
        '''Lit les données du capteur HIH8121
        '''
        vals = self.i2c.readfrom(0x0, 4) # read 4 bytes from the sensor
        # data bytes as defined in datasheet
        db1 = vals[0] & 0xFF
        db2 = vals[1] & 0xFF
        db3 = vals[2] & 0xFF
        db4 = vals[3] & 0xFF

        status = (db1 & 0xC0) >> 6
        humidityRaw = db2 + ((db1 & 0x3F) << 8)
        tempRaw = (db3 << 6) + ((db4 >> 2) & 0x3F)

        self.humidity = (humidityRaw / 16383.0) * 100
        self.temperature = (165 * (tempRaw / (16383.0))) - 40
        return self.humidity, self.temperature
