
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
import logging
from cuve_fuel import CuveFuel
from credentials import CREDENTIALS

time.sleep(5)

cuve_fuel = CuveFuel(lidar_min=20, lidar_max=800, lida_freq=100,
                     pin_sda=8, pin_scl=9, i2c_freq=400_000, 
                     pin_led_rouge=1, pin_led_vert=0)

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "T-HOME/CUVE-FUEL2",
    watchdog=100,
    sysinfo_period = 600,
    led_wifi='LED',
    name = "Cuve de Fuel",
    logging_level=logging.INFO,
    device=cuve_fuel
    )

iot.run()