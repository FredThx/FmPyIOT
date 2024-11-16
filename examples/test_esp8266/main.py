import time
from machine import Pin
import logging

if False:
    from fmpyiot.fmpyiot import FmPyIot
    from fmpyiot.topics import Topic

    from credentials import CREDENTIALS

    time.sleep(5)

    iot = FmPyIot(
        mqtt_host = CREDENTIALS.mqtt_host,
        ssid = CREDENTIALS.wifi_SSID,
        password = CREDENTIALS.wifi_password,
        mqtt_base_topic = "T-HOME/TEST_ESP8266",
        watchdog=300,
        sysinfo_period = 600,
        led_wifi=None,
        web=True,
        name = "Un test pour ESP8266",
        logging_level=logging.INFO,
        )

    led = Pin(2) # Attention 0: allumée, 1=éteint

    test_action = Topic("./test", action=lambda payload, topic: led(not payload))
    test_read = Topic("./read", read = 42, send_period=20)

    iot.add_topic(test_action)
    iot.add_topic(test_read)

    iot.run()