#from devices.ds18b20 import DS18b20
#from devices.fdht import DHT22
from machine import Pin, SPI, I2C
from dht import DHT22
import logging

from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicRoutine, TopicRead

from devices.mcp3008 import MCP3008
from devices.capacitive_soil_moisture_sensor import Hygrometer  
from devices.motor_I298 import MotorI298
from devices.tsl2561 import TSL2561
from devices.lps35hw import LPS35HW
from devices.bmp085 import BMP180


from soil_moistures import SoilMoistures
from vanne import Vanne
#from reservoir import Reservoir

from credentials import CREDENTIALS

# Bus SPI et I2C
spi = SPI(0, baudrate=100000, polarity=0, phase=0, bits=8, sck=Pin(6), mosi=Pin(7), miso=Pin(4))
i2c = I2C(0,sda=Pin(8), scl=Pin(9), freq=100000)

# Capteurs d'humidité de sol capacitifs
can =  MCP3008(spi, cs = Pin(5), ref_voltage=5.0)
soil_moistures = SoilMoistures(
    [Hygrometer(lambda i=i:can.read(i), a_min=550, a_max=220, name=f"Hydrometer_{6-i}") for i in range(6)]
    )
# Vanne d'arrosage
motor=MotorI298(pinA=Pin(17), pinB=Pin(18), pin_ena=Pin(16)) # Moteur de la vanne
vanne = Vanne(
    motor = motor,
    pin_open=Pin(15, Pin.IN), # capteur à effet Hall pour vérifier si la vanne est ouverte
    pin_close=Pin(14, Pin.IN), # capteur à effet Hall pour vérifier si la vanne est fermée
    timeout=3000, # Timeout en ms = temps maxi pour que la vanne s'ouvre/ferme
    delay=5, # Délai en ms entre chaque vérification de l'état de la vanne
)
# Capteur humidité air + température DHT22
dht = DHT22(Pin(1))

#Capteur Luminosité TLS2561
tls2561 = None
# Fonction de lecture du capteur de luminosité TSL2561
def read_luminosite():
    global tls2561
    if tls2561 is None:
        try:
            tls2561 = TSL2561(i2c, address=0x39)
        except OSError:
            print("TSL2561 not found")
    if tls2561:
        try:
            return tls2561.read(autogain=True)
        except OSError:
            logging.error("Error reading TLS2561:")
            tls2561 = None
        except ValueError as e:
            logging.error(f"ValueError reading TLS2561: {e}")
    return 0.0

# Reservoir d'eau
#lps = LPS35HW(i2c, address=0x5D)  # Capteur de pression au fond du réservoir
#bmp = BMP180(i2c, address=0x77)  # Capteur de pression hors du réservoir
#reservoir = Reservoir(lps, bmp, max_height=100, name="reservoir")

#Création de l'IOT avec interface web et mécanismes MQTT
iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/SERRE/",
    led_wifi= Pin("LED", Pin.OUT), # LED de connexion WiFi = internal LED
    watchdog=100,
    sysinfo_period = 600,
    logging_level= logging.INFO,
    name="La Serre de Fred",
    description="Le pilotage de la serre (vanne, capteurs d'humidité de sol, etc.)",
    )
#Liens entre les capteurs et l'IOT

soil_moistures.set_iot(iot)
vanne.set_iot(iot)

#reservoir.set_iot(iot)

iot.add_topic(Topic("./temperature", read=lambda topic, payload : dht.temperature(), send_period=30))
iot.add_topic(Topic("./humidity", read = lambda topic, payload : dht.humidity(), send_period=30))
iot.add_topic(TopicRoutine(dht.measure, send_period=10))

iot.add_topic(TopicRead("./LUMINOSITE", read=read_luminosite, send_period=10))

#Main loop
iot.run()
