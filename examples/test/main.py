
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
import logging
from machine import Pin
from credentials import CREDENTIALS

time.sleep(5)

assert len([])==0, "Error with len!"

def render():
    heure = '%s-%s-%s %s:%s:%s'%(time.localtime()[:6])
    return f"""<H3>Hello World!</H3>
        <p>This is the main web page rendered by the render_web function.</p>
        <p>Current Time: {heure}</p>"""

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