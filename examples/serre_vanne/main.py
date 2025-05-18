#from devices.ds18b20 import DS18b20
#from devices.fdht import DHT22
from machine import Pin
from fmpyiot.fmpyiot_web import FmPyIotWeb
from devices.motor_I298 import MotorI298
from vanne import Vanne
from credentials import CREDENTIALS

assert len([])==0, "Error with len!"

motor = MotorI298(Pin(17),Pin(18),Pin(16))
vanne = Vanne(motor=motor, pin_open=Pin(15), pin_close = None, timeout=2000, delay=5)

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/SERRE/VANNE",
    watchdog=100,
    sysinfo_period = 600,
    name="Vanne de la Serre de Fred",
    description="Une vanne pour arrosage",
    )

vanne.set_iot(iot)
iot.run()