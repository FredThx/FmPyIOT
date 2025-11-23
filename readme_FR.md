[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/FredThx/FmPyIOT/blob/master/readme.md)[![fr](https://img.shields.io/badge/lang-fr-blue.svg)](https://github.com/FredThx/FmPyIOT/blob/master/readme_FR.md)

# projet Fmpyiot

Pour des projets micropython sur des microcontroleurs.

C'est une évolution de https://github.com/FredThx/nodemcu_iot

Mais en micropython (et non plus en Lua)

L'idée est d'avoir une libriairie commune pour gérer des objects connectés à base de microcontroleur (raspberry pi pico, esp32, ...) compatibles avec micropython.

Ensuite, les communications se font en WIFI + MQTT.

En option : accès en http

## Principes

Un projet se décrit à partir d'un fichier main.py dans lequel on va décrire son fonctionement

Exemples

Exemple n°1 : les topics dans le main.py

```python
from devices.mydevice import MyDevice

from fmpyiot.fmpyiot import FmPyIot
from fmpyiot.topics import Topic

mydevice = Mydevice()

iot = FmPyIot(  
    mqtt_host = "....",
    mqtt_base_topic = "....",
    ssid = '....',
    password = "....",
    watchdog = 100,
    sysinfo_period = 600,
    led_incoming = None,
    led_wifi = None,
    web=True,
    web_credentials=("login", "password"),
    name = "FmPyIot TEST",
)
# En mode synchrone (lecture du capteur rapide)
ma_mesure = Topic("./ma_mesure", read=lambda topic, payload : mydevice.read(), send_period=60)
iot.add_topic(ma_mesure)

# En mode asynchrone (si la lecture du capteur est longue, ou pour le style)
async def co_mesure():
    #Long traitement
    await asyncio.sleep(3)
    return 42
iot.add_topic(Topic('/CO_TEST', read = co_mesure))

iot.run()
```

Example n°2 : avec un objet Device

https://github.com/FredThx/FmPyIOT/blob/master/examples/test_render_web_gpio_status/test.py

https://github.com/FredThx/FmPyIOT/blob/master/examples/test_render_web_gpio_status/main.py



my_device.py

```python
import time
from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import Topic, TopicIrq
from fmpyiot.device import Device
from machine import Pin
from pico_render import PicoRender

class MyDevice(Device):
    '''
    Class representing my device : a test 
    '''
    params = {
        "output_pin": 10,
    }

    def __init__(self, input_pin:int, output_pin:int=None, name:str="TEST FmPyIot"):
        '''
        input_pin : digital input Pin
        Output_pin : digital output Pin
        '''
        super().__init__(name)
        self.input_pin = Pin(input_pin, Pin.IN, Pin.PULL_UP)
        if output_pin is not None:
            self.params["output_pin"] = output_pin
        self.pico_render = PicoRender("<h4>GPIO Status</h4>")
        self.load_params()
  
    def on_load_params(self):
        '''Called on load_params and when parameters are changed'''
        self.output_pin = Pin(self.params["output_pin"], Pin.OUT)

    def set_iot(self, iot:FmPyIotWeb):
        '''Crée les topics MQTT pour gérer les GPIO
        1 topic IRQ pour l'input_pin
        1 topic de lecture pour l'output_pin qui est envoyé toutes les secondes
        1 topic action pour simuler une pression sur le bouton via MQTT
        '''
        super().set_iot(iot)
        iot.add_topic(TopicIrq(f"./INPUT", pin=self.input_pin, trigger=Pin.IRQ_FALLING, values=("PRESSED","RELEASED"), on_irq=self.on_pressed,tempo_after_falling=1))
        iot.add_topic(Topic(f"./OUTPUT", read=lambda:self.output_pin(), send_period=1))
        iot.add_topic(Topic(f"./PRESS", action=self.on_pressed))

    def on_pressed(self):
        '''Toggle the output pin
        '''
        self.output_pin(not self.output_pin())  

    def render_web(self)->str:
        '''Renders the web page content
        '''
        heure = '%s-%s-%s %s:%s:%s'%(time.localtime()[:6])
        html = f"""<br><H3>Etat du FmPyIot</H3>
            <p>Current Time: {heure}</p>
            {self.pico_render.render()}    """
        return html
```

## Installation

- Installez micropython sur votre µcontroleur.
- Uploader [/lib]()
- Uploader [/FmPyIot]()
- créer un fichier ``boot.py`` vide
- créer un fichier ``main.py`` selon l'exemple ci-dessus
  - avec IP du broker MQTT
  - SSID et pass de votre réseau WIFI
  - ...
  - créer les topics
  - ajouter les topics
  - créer des paramètres
- boot le µc

## Description

### MAGICS TOPICS

### Les topics system

#### ./SYSINFO

Renvoie les données system

```json
{"ifconfig":["192.168.10.77","255.255.255.0","192.168.10.254","192.168.10.169"],"uname":["rp2","rp2","1.21.0","v1.21.0 on 2023-10-06 (GNU 13.2.0 MinSizeRel)","Raspberry Pi Pico W with RP2040"],"mac":"28:cd:c1:0f:4d:81","wifi":{"ssid":"WIFI_THOME2","channel":3,"txpower":31},"mem_free":119504,"mem_alloc":57776,"statvfs":[4096,4096,212,118,118,0,0,0,0,255]}
```

### ./PARAMS

Renvoie les paramètres

### ./SET_PARAM

Permet de modifier un paramètre.

### ./SET_PARAMS

Permet de modifier les paramètres.

#### Reverse topic

Pour chaque topic "TOPIC", un reverse topic est généré : "TOPIC_" qui force l'envoie du topic.

Si un topic est prévu en message sortant (ex : lecture d'un capteur), alors un topic permet de forcer la lecture de cette valeur.

Si un topic est prévu en message entrant (ex : l'execution d'une action), alors un topic est créé pour récupérer la valeur de retour de l'action (ex : "OK" ou une valeur)

|                      | MQTT entrant | MQTT sortant                          |
| -------------------- | ------------ | ------------------------------------- |
| Topic read "./TEMP"  | ./TEMP_      | ./TEMP                                |
| Topic action "./LED" | ./LED        | ./LED_ (si action renvoie une valeur) |
| Topic system SYSINFO | SYSINFO_     | SYSINFO                               |

## Serveur web

### Visualiser les valeurs des Topics / Exécuter les actions

![topics](image/readme/topics.png)

### visualiser les informations system

![sysinfo](image/readme/sysinfo.png)

### Modifier des paramètres

![files](image/readme/params.png)

### Upload/download les fichiers

![files](image/readme/files.png)

### avoir une console REPL

![repl](image/readme/repl.png)

### un petit menu system

![system](image/readme/system.png)

## API

le microcontrôleur et le navigateur internet communiquent à travers cette API :

Sécurité : BasicAutentification

|                                     | Method          | url                                                                                                | params                                                                              | output                                                |
| ----------------------------------- | --------------- | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------- |
| Les topics en HTML                  | GET             | /api/topics                                                                                        |                                                                                     | code HTML de la page topics                           |
| Le status de l'IOT                  | GET             | /api/status                                                                                        |                                                                                     | json de sysinfo                                       |
| Liste des fichiers                  | GET             | /api/ls                                                                                            |                                                                                     | json:``json {'files' : ['main.py', 'boot.py', ....}`` |
| Download fichier                    | GET             | /api/download/{nom du fichier}                                                                     |                                                                                     |                                                       |
| Delete fichier                      | DELETE          | /api/delete/{nom_fichier}                                                                          |                                                                                     | 200, OK                                               |
| Upload fichier                      | PUT             | /api/upload/{nom_fichier}}                                                                         | fichier binary                                                                      | 201, Created                                          |
| Reboot                              | GET&#124; POST | /api/reboot                                                                                        |                                                                                     | 200, Ok                                               |
| Met le µc en mode bootloader       | GET&#124; POST | /api/bootloader                                                                                    |                                                                                     | 200, Ok                                               |
| Execute une action d'un topic       | POST            | /api/action/{topic_id}<br />``topic_id = "T"+re.sub(r'\W','_',self.topic)``                       | json:``json {'topic' : ..., 'payload':...}``<br />Souvent topic est ici facultatif | 200,OK                                                |
| Les dernières lignes de la console | GET             | /api/repl                                                                                          |                                                                                     | json:``json {"repl" : ['...', '...', ...]}``          |
| Execution d'une commande python     | POST            | /api/repl/cmd                                                                                      | json:``json {"cmd" : "print(f'Hello {iot.name}')"}``                                | json:``json {"rep": ""}``                            |
| Niveau du logging                   | POST            | /api/logging-level/{level}<br />level = 10 (DEBUG), 20(INFO), 30(WARNING), 40(ERROR), 50(CRITICAL) |                                                                                     | 200, OK                                               |
| Hello                               | GET             | /api/hello                                                                                         |                                                                                     | "FmPyIOT"""                                           |
| Contenu du dernier fichier log      | GET             | /api/logs                                                                                          |                                                                                     |                                                       |
| Liste des paramètres               | GET             | /api/param                                                                                         |                                                                                     |                                                       |
| Supprime un paramètre              | DELETE          | /api/params/delete/{param_to_delete}                                                               |                                                                                     | 200, OK                                               |

# Thanks

[https://github.com/hugokernel/micropython-nanoweb]()

[https://github.com/peterhinch/micropython-mqtt]()
