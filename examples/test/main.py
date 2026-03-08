
import time
from test import Test
from fmpyiot.fmpyiot_web import FmPyIotWeb
import logging
from credentials import CREDENTIALS
from fmpyiot.topics import Topic, TopicRoutine, TopicIrq, TopicOnChange, TopicAction

time.sleep(5)

test = Test()

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    mqtt_queue_len = 1,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/TEST",
    watchdog=None,
    sysinfo_period = 600,
    led_wifi='LED',
    name = "Test TopicOnChange",
    logging_level=logging.INFO,
    devices=[test]
    )

iot.run()