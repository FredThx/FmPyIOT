
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
import logging
from on_change import OnChange
from credentials import CREDENTIALS

time.sleep(5)

device = OnChange(pin_adc=27)

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/TEST",
    watchdog=None,
    sysinfo_period = 600,
    led_wifi='LED',
    name = "Test TopicOnChange",
    logging_level=logging.INFO,
    device=device
    )

iot.run()