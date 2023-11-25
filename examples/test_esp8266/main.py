
if False:
    import time
    from machine import Pin
    from fmpyiot.fmpyiot import FmPyIot
    from fmpyiot.topics import Topic
    import logging
    time.sleep(5)

    iot = FmPyIot(
        mqtt_host = "***REMOVED***",
        mqtt_base_topic = "T-HOME/TEST_ESP8266",
        ssid = 'WIFI_THOME2',
        password = "***REMOVED***",
        watchdog=300,
        sysinfo_period = 600,
        led_wifi=None,
        web=True,
        web_credentials=(***REMOVED***, ***REMOVED***),
        name = "Un test pour ESP8266",
        logging_level=logging.INFO,
        )

    led = Pin(2) # Attention 0: allumée, 1=éteint

    test_action = Topic("./test", action=lambda payload, topic: led(not payload))
    test_read = Topic("./read", read = 42, send_period=20)

    iot.add_topic(test_action)
    iot.add_topic(test_read)

    iot.run()