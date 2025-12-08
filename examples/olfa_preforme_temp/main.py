import time, logging
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic
from devices.ds18b20 import DS18b20
from credentials import CREDENTIALS

class Thermometre:
    def __init__(self):
        self.ds = DS18b20(27)
        self.params = {
            'temperature_offset' : 0
        }
    
    async def get_temperature(self, **kwargs):
        raw_temp = await self.ds.read_async()
        if raw_temp is None:
            return None
        else:
            return raw_temp + float(self.params['temperature_offset'])

    def load_params(self, param:dict):
        self.params.update(param)
    
thermometre = Thermometre()

time.sleep(5)

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "OLFA/PREFORMES/THERMOMETRE",
    watchdog=100,
    sysinfo_period = 600,
    led_wifi="LED",
    web=True,
    name = "Thermometre Préformes",
    logging_level=logging.INFO,
    )

iot.set_param('thermometre', default=thermometre.params, on_change=thermometre.load_params)

topic_temperature = Topic("./temperature",
                          read=thermometre.get_temperature,
                          send_period=30)

iot.add_topic(topic_temperature)

iot.run()

