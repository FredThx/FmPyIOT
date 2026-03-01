from machine import Pin, SPI, I2C

import logging

from fmpyiot.fmpyiot_web import FmPyIotWeb

from devices.mcp3008 import MCP3008
from devices.capacitive_soil_moisture_sensor import Hygrometer  
from devices.motor_I298 import MotorI298

from soil_moistures import SoilMoistures
from vanne import Vanne
from serre_meteo import Meteo

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
#Données météo
meteo = Meteo(dht_pin=1, i2c=i2c, tls2561_address=0x39, name="Météo Serre")

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
    devices=[soil_moistures, vanne, meteo],
    )

#Main loop
iot.run()
