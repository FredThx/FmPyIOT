#from devices.ds18b20 import DS18b20
#from devices.fdht import DHT22
from dht import DHT22 
from devices.tsl2561 import TSL2561
from machine import Pin, I2C
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicRoutine, TopicRead

from credentials import CREDENTIALS

assert len([])==0, "Error with len!"


dht = DHT22(Pin(18))

i2c = I2C(1,sda=Pin(26), scl=Pin(27), freq=100000)
try:
    sensor = TSL2561(i2c, address=0x39)
except OSError:
    sensor = None
    print("TSL2561 not found")

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/SERRE",
    watchdog=100,
    sysinfo_period = 600,
    name="Serre de Fred",
    description="Une petite serre pour des salades.",
    )

iot.add_topic(Topic("./temperature", read=lambda topic, payload : dht.temperature(), send_period=30))
iot.add_topic(Topic("./humidity", read = lambda topic, payload : dht.humidity(), send_period=30))
iot.add_topic(TopicRoutine(dht.measure, send_period=5))

def read_sensor():
    global sensor
    if sensor is None:
        try:
            sensor = TSL2561(i2c, address=0x39)
        except OSError:
            print("TSL2561 not found")
    if sensor:
        try:
            return sensor.read()
        except OSError:
            print("Error reading sensor:")
            sensor = None
    return 0.0

iot.add_topic(TopicRead("./LUMINOSITE", read=read_sensor, send_period=10))


iot.run()