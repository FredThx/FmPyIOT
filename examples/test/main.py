
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
import logging
from credentials import CREDENTIALS
from fmpyiot.topics import Topic, TopicRoutine, TopicIrq, TopicOnChange, TopicAction

time.sleep(5)


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
    )

compteur = 0
def my_routine(topic, payload):
    global compteur
    compteur += 1
    #time.sleep(0.2) # Simulate a long processing time

iot.add_topic(Topic("./test",send_period=1, read=lambda :compteur+0))
iot.add_topic(TopicAction("./test", action=lambda topic, payload: print("****************  Reception :", payload)))
# Une routine pour saturer le µC
iot.add_topic(TopicRoutine(topic="./test_routine", send_period=0, action=my_routine))

iot.run()