# Energyzero-naar-P1-monitor
Importeer de gemiddelde dag prijs voor elektra en gas van Energyzero naar P1 monitor

Getest op P1 MONITOR VERSIE 20221105 – 2.1.0

Voorbereiding :

Log in op de P1 monitor : sudo ssh p1mon@192.168.1.21

Check Python versie : p1mon@p1monitor(eth0=192.168.1.10 wlan0=): ~$ python --version

Python versie moet zijn : Python 3.9.2

Installeer energyzero module : p1mon@p1monitor(eth0=192.168.1.10 wlan0=): ~$ pip install energyzero
