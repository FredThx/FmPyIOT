# projet Fmpyiot

Pour Fred, micropython IOT

C'est une évolution de https://github.com/FredThx/nodemcu_iot

mais en micropython (et non plus en Lua)

L'idée est d'avoir une libriairie commune pour gérer des objects connectés à base de microcontroleur (raspberry pi pico, esp32, ...) compatibles avec micropython.

Ensuite, les communications se font en WIFI + MQTT.

# Principes

Un projet se décrit à partir d'un fichier main.py dans lequel on va décrire son fonctionement

Exemple
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
    watchdog=100,
    sysinfo_period = 600,
    async_mode=False)

ma_mesure = Topic("./ma_mesure", read=lambda topic, payload : mydevice.read(), send_period=60)

while not iot.connect():
    print("Erreur lors de la connexion.... on retente!")
iot.add_topic(distance)
iot.add_topic(temperature)
iot.run()
```

# Description

## MAGICS TOPICS

Pour chaque topic "TOPIC", un reverse topic est généré : "TOPIC_" qui force l'envoie du topic.

./SYSINFO_    =>  ./SYSINFO
