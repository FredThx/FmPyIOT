#from devices.ds18b20 import DS18b20
#from devices.fdht import DHT22
from machine import Pin
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicRoutine, TopicAction
from devices.motor_stepper import StepperMotor
from vanne import Vanne
from credentials import CREDENTIALS

assert len([])==0, "Error with len!"


vanne = Vanne(StepperMotor([Pin(2), Pin(3), Pin(4), Pin(5)], delay=5, half_step=True))

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/SERRE/VANNE",
    watchdog=100,
    sysinfo_period = 600,
    name="Vanne de la Serre de Fred",
    description="uenvanne pour arrosage",
    )

iot.add_topic(TopicAction("./open", on_incoming=vanne.open))
iot.add_topic(TopicAction("./close", on_incoming=vanne.close))
async def move(topic, payload):
    await vanne.move(payload)
iot.add_topic(TopicAction("./move", on_incoming=move))


iot.run()