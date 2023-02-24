# Energyzero prijzen naar P1-monitor
Importeer de actuele prijs voor elektra en gas van Energyzero naar P1 monitor

Getest op P1 MONITOR VERSIE 20221105 – 2.1

OPMERKING : Lees eerst voorbereiding_op_p1mon.txt
--------------------------------------------------------------------------------

Reactie van Security Brother / ztatz.nl 

Je update in de code ook de /p1mon/data/config.db dat hoeft niet de datauit de ram database wordt automatisch gekopieerd door de p1 software.
with sqlite3.connect(“/p1mon/data/config.db”) as sqlite_connection: Als voorbeeld hoeft dus niet.

De code ziet er netjes uit, mijn complimenten. Als er voldoende vraag naar is en je staat het toe dan kan het een standaard onderdeel worden van de p1 monitor software.

-------------------------------------------------------------------------------

# Energyzero prices to P1 monitor

Import the actual price for electricity and gas from Energyzero to P1 monitor.

Tested on P1 MONITOR VERSION 20221105 - 2.1

NOTE: Please read voorbereiding_op_p1mon.txt first.

--------------------------------------------------------------------------------
