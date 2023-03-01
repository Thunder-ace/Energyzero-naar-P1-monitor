# Energyzero prijzen naar P1-monitor
Importeer de actuele prijs voor elektra en gas van Energyzero naar P1 monitor

Getest op P1 MONITOR VERSIE 20221105 – 2.1 LET OP ! Dit is een add-on die NIET onder de verantwoordelijkheid valt van ztatz.nl. Gebruik is voor eigen risico en maak ALTIJD eerst een BACKUP van de P1 monitor !!!

OPMERKING : Lees eerst voorbereiding_op_p1mon.txt

Toegevoegd installatie script : in terminal run : python3 install.py
Zorg dat prijzen.py of prijzen_salderen.py in dezelfde map staat als install.py
Lees de opmerkingen in het script en pas aan waar nodig.

--------------------------------------------------------------------------------

Reactie van Security Brother / ztatz.nl 

Je update in de code ook de /p1mon/data/config.db dat hoeft niet de datauit de ram database wordt automatisch gekopieerd door de p1 software.
with sqlite3.connect(“/p1mon/data/config.db”) as sqlite_connection: Als voorbeeld hoeft dus niet.

De code ziet er netjes uit, mijn complimenten. Als er voldoende vraag naar is en je staat het toe dan kan het een standaard onderdeel worden van de p1 monitor software.

--------------------------------------------------------------------------------

# Energyzero prices to P1 monitor

Import the actual price for electricity and gas from Energyzero to P1 monitor.

Tested on P1 MONITOR VERSION 20221105 - 2.1

NOTE: Please read voorbereiding_op_p1mon.txt first.

--------------------------------------------------------------------------------

Response from Security Brother / ztatz.nl:

In the code, you also update /p1mon/data/config.db. This is not necessary as the data from the RAM database is automatically copied by 
the P1 software with sqlite3.connect("/p1mon/data/config.db") as sqlite_connection. So, this example is not needed.

The code looks neat, my compliments. If there is enough demand and you allow it, it could become a standard part of the P1 monitor software.

--------------------------------------------------------------------------------
