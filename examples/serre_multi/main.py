#from devices.ds18b20 import DS18b20
#from devices.fdht import DHT22
from machine import Pin, SPI
from fmpyiot.fmpyiot_web import FmPyIotWeb
from devices.mcp3008 import MCP3008
from devices.capacitive_soil_moisture_sensor import Hygrometer  
from soil_moistures import SoilMoistures
from credentials import CREDENTIALS
import logging

try:
    len([])
except:
    del len

spi = SPI(0, baudrate=100000, polarity=0, phase=0, bits=8, sck=Pin(6), mosi=Pin(7), miso=Pin(4))
can =  MCP3008(spi, cs = Pin(5), ref_voltage=5.0)
soil_moistures = SoilMoistures(
    [
        Hygrometer(lambda :can.read(0), a_min=550, a_max=220, name=f"Hydrometer_1"),
        Hygrometer(lambda :can.read(1), a_min=550, a_max=220, name=f"Hydrometer_2"),
        #Hygrometer(lambda :can.read(2), a_min=550, a_max=220, name=f"Hydrometer_3"),
        #Hygrometer(lambda :can.read(3), a_min=550, a_max=220, name=f"Hydrometer_4"),
        #Hygrometer(lambda :can.read(4), a_min=550, a_max=220, name=f"Hydrometer_5"),
        #Hygrometer(lambda :can.read(5), a_min=550, a_max=220, name=f"Hydrometer_6"),
    ]
    )

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/SERRE/HYDROS",
    watchdog=100,
    sysinfo_period = 600,
    logging_level= logging.INFO,
    name="Hydrometres de la Serre de Fred",
    description="Des capteurs d'humidité de sol capacitifs.",
    )

soil_moistures.set_iot(iot)
iot.run()
