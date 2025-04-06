import time, logging, uasyncio as asyncio
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicIrq, TopicAction, TopicRoutine
from devices.ds18b20 import DS18b20
from devices.Pico_lcd_1_44 import LCD_1inch44
from devices.display import Display, Field, RIGHT
from machine import Pin
from credentials import CREDENTIALS

class Etuve:
    def __init__(self, lcd:LCD_1inch44=None,
                 ds_pin:int=None,
                 relais_pin:int=None,
                 button_start_pin:int=None,
                 button_stop_pin:int=None,
                 button_add_time_pin:int=None,
                 button_sub_time_pin:int=None,
                 step:int=1):
        self.disp = Display(lcd) if lcd else None
        self.ds = DS18b20(ds_pin) if ds_pin else None
        self.relais = Pin(relais_pin, Pin.OUT) if relais_pin else None
        if self.relais:
            self.relais.value(0) # relais off by default
        self.button_add_time = Pin(button_add_time_pin, Pin.IN, Pin.PULL_UP) if button_add_time_pin else None
        self.button_sub_time = Pin(button_sub_time_pin, Pin.IN, Pin.PULL_UP) if button_sub_time_pin else None
        self.button_start = Pin(button_start_pin, Pin.IN, Pin.PULL_UP) if button_start_pin else None
        self.button_stop = Pin(button_stop_pin, Pin.IN, Pin.PULL_UP) if button_stop_pin else None
        self.step = step
        self.stop_time = None # time to stop the etuve
        self.params = {
            'temperature_offset' : 0,
            'duration' : 60, # duration in minutes
        }
        self.init_lcd()
    
    def set_iot(self, iot:FmPyIotWeb):
        self.iot = iot
        self.iot.add_topic(TopicIrq(topic = "./bt_add_time", pin = self.button_add_time, on_irq = lambda : self.add_time(self.step), trigger=Pin.IRQ_FALLING))
        self.iot.add_topic(TopicIrq(topic = "./bt_sub_time", pin = self.button_sub_time, on_irq = lambda : self.add_time(-self.step), trigger=Pin.IRQ_FALLING))
        self.iot.add_topic(TopicIrq(topic = "./bt_start", pin = self.button_start, on_irq = self.start_timer, trigger=Pin.IRQ_FALLING))
        self.iot.add_topic(TopicIrq(topic = "./bt_stop", pin = self.button_stop, on_irq = self.stop_timer, trigger=Pin.IRQ_FALLING))
        #for pin in [self.button_add_time, self.button_sub_time, self.button_start, self.button_stop]:
        #        pin.init(pull=Pin.PULL_UP) # Je ne sais pas pourquoi il faut réinitialiser le pull-up
        self.iot.set_param('etuve', default=self.params, on_change=self.load_params)
        self.iot.add_topic(Topic("./temperature", read=self.get_temperature, send_period=30))
        self.iot.add_topic(TopicAction("./set_timer", on_incoming=self.on_set_timer))
        self.iot.add_routine(self.check_timer)
        self.iot.add_routine(self.update_lcd)



    async def get_temperature(self, **kwargs):
        if self.ds:
            raw_temp = await self.ds.read_async()
            return raw_temp + float(self.params['temperature_offset']) if raw_temp else 0.0
        else:
            return 0.0
    
    def set_relais(self, state:bool):
        logging.info(f"Set relais to {state}")
        if self.relais:
            self.relais.value(state)
    
    def on_set_timer(self, topic:str, payload:str|float):
        logging.info(f"Set timer to {payload}") 
        if payload:
            self.start_timer()
        else:
            self.stop_timer()

    def add_time(self, time_m:int):
        '''if timer is on, add time in minutes to the stop time
        else add time to the duration'''
        logging.info(f"Add time {time_m} minutes")
        if self.stop_time:
            self.stop_time += time_m*60
            self.stop_time = max(self.stop_time, time.time())
        else:
            self.params['duration'] += time_m
            self.params['duration'] = max(self.params['duration'], 0)
            self.iot.params.set_param('etuve', self.params)

    def start_timer(self, duration_m :int=None):
        logging.info(f"Start timer for {duration_m} minutes")
        duration_m = duration_m or self.params['duration']
        '''Start the etuve for a duration in minutes'''
        self.stop_time = time.time() + int(duration_m*60)
        self.set_relais(True)

    def stop_timer(self):
        '''Stop the etuve'''
        logging.info("Stop timer")
        self.stop_time = None
        self.set_relais(False)

    async def check_timer(self):
        '''Check if the etuve should stop'''
        while True:
            logging.debug("Check time")
            if self.stop_time and time.time() > self.stop_time:
                self.stop_timer()
            await asyncio.sleep(1)

    def load_params(self, param:dict):
        logging.info(f"Load params : {param}")
        for k, v in param.items():
            try:
                self.params[k] = float(v)
            except ValueError:
                pass
        self.params.update(param)

    def init_lcd(self):
        logging.info("Init LCD")
        if self.disp:
            self.disp.device.fill(self.disp.device.BLACK)
            self.disp.device.show()
            self.disp.text("start",1,11, self.disp.device.WHITE)
            self.disp.text("stop",5,12, self.disp.device.WHITE)
            self.disp.text("+",9,15, self.disp.device.WHITE)
            self.disp.text("-",13,15, self.disp.device.WHITE)
            #self.disp.set_field("Temperature", Field("Temp:", 1,1,width=3, unit='C', align=RIGHT, color=self.disp.device.WHITE))
            self.disp.text("Consigne", 3,0, self.disp.device.GREEN)
            self.disp.set_field("Duration", Field("", 4,0,width=8, align=RIGHT, color=self.disp.device.GREEN))
            self.disp.text("Reste", 6,0, self.disp.device.RED)
            self.disp.set_field("time_remaning", Field("", 7,0,width=8, align=RIGHT, color=self.disp.device.RED))
            self.disp.update()

    async def update_lcd(self):
        if self.disp:
            while True:
                #logging.info("Update LCD")
                temperature = await self.get_temperature()
                #self.disp.set("Temperature", str(temperature))
                self.disp.set("Duration", self.hh_mm_ss(self.params['duration']))
                self.disp.set("time_remaning", self.hh_mm_ss(max(0,self.stop_time-time.time()) if self.stop_time else 0))
                await asyncio.sleep(0.2)

    def hh_mm_ss(self, seconds:int):
        '''Convert seconds to hh:mm:ss'''
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
    
etuve = Etuve(
    lcd = LCD_1inch44(),
    #ds_pin=27,
    relais_pin=6,
    button_start_pin=3, button_stop_pin=2, button_add_time_pin=17, button_sub_time_pin=15,
    step = 5)

iot = FmPyIotWeb(
    mqtt_host = CREDENTIALS.mqtt_host,
    ssid = CREDENTIALS.wifi_SSID,
    password = CREDENTIALS.wifi_password,
    web_credentials=(CREDENTIALS.web_user, CREDENTIALS.web_password),
    mqtt_base_topic = "OLFA/IMPREGNATION/ETUVE",
    watchdog=100,
    sysinfo_period = 600,
    led_wifi="LED",
    web=True,
    name = "Etuve imprégnation",
    logging_level=logging.INFO,
    )

etuve.set_iot(iot)

iot.run(wait = 5)

