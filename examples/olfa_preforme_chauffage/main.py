import time, logging, uasyncio as asyncio
from machine import Pin
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicIrq, TopicAction
from credentials import CREDENTIALS

relay = Pin(6, Pin.OUT)

time.sleep(5)

def render_web()->str:
    state = "ON 🔥" if relay.value() else "OFF 💧"
    html = f"""
    <h2>Chauffage Préformes</h2>
    <p>État du chauffage : <strong>{state}</strong></p>
    """
    return html



iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "OLFA/PREFORMES/CHAUFFAGE",
    watchdog=100,
    sysinfo_period = 600,
    led_wifi="LED",
    web=True,
    name = "Chauffage Préformes",
    logging_level=logging.INFO,
    render_web=render_web
    )

iot.add_topic(TopicAction("./chauffe", on_incoming=lambda topic, payload : relay(payload.upper()=="ON")))

iot.run()

