
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
import logging
from machine import Pin
from credentials import CREDENTIALS
from pico_render import PicoRender

time.sleep(5)

assert len([])==0, "Error with len!"

pico_render = PicoRender("<h4>GPIO Status</h4>")

def render():
    heure = '%s-%s-%s %s:%s:%s'%(time.localtime()[:6])
    return f"""<br><H3>Etat du FmPyIot</H3>
        <p>Current Time: {heure}</p>
        {pico_render.render()}
        """

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/TEST",
    watchdog=None,
    sysinfo_period = 600,
    
    led_wifi='LED',
    web=True,
    name = "TEST",
    logging_level=logging.DEBUG,
    render_web=render,
    )


iot.run()