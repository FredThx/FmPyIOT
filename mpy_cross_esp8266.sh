compiler=/mnt/c/Devlopp/micropython-1.22.0/mpy-cross/build/mpy-cross
sudo $compiler -march=xtensa fmpyiot/fmpyiot.py
sudo $compiler -march=xtensa fmpyiot/topics.py
sudo $compiler -march=xtensa fmpyiot/wd.py
sudo $compiler -march=xtensa lib/logging/__init__.py
sudo $compiler -march=xtensa lib/logging/handlers.py
sudo $compiler -march=xtensa lib/mqtt_as/mqtt_as.py
