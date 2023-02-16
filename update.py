#!/usr/bin/python

import os
import sqlite3
import subprocess
import datetime

# Check of internet bereikbaar is
wan_connected = False
while not wan_connected:
    ping_output = subprocess.check_output(['ping', '-4', '-c', '1', '-w', '2', '208.67.222.222'])
    if b'1 received' in ping_output:
        wan_connected = True
        print('Internet is bereikbaar.')
        try:
            result       = subprocess.run(['python3', '/p1mon/scripts/stroom.py'], capture_output=True, text=True)
            lines        = result.stdout.strip().split('\n')
            last_line    = lines[-1]
            stroom_prijs = "{:.2f}".format(float(last_line))
            print(stroom_prijs)
        except:
            print('Fout bij het ophalen van Energyzero stroomprijs.')
            exit()    
        # Start subprocess en haal de gas prijs op
        try:
            result = subprocess.run(['python3', '/p1mon/scripts/gas.py'], capture_output=True, text=True)
            lines     = result.stdout.strip().split('\n')  # Split het resultaat en pak het laatste woord
            last_line = lines[-1]
            gas_prijs = "{:.2f}".format(float(last_line))  # Gas prijs naar twee cijfers achter de komma
            print(gas_prijs)
        except:
            print('Fout bij het ophalen van Energyzero gasprijs.')
            exit()
    else:
        print('Fout, internet niet bereikbaar !')
        exit()

def update_config():
    # Functie voor update config.db met nieuwe prijzen
    try:
        sqliteConnection    = sqlite3.connect("/p1mon/mnt/ramdisk/config.db")   # Verbind met config.db
        cursor              = sqliteConnection.cursor()
        # voeg de nieuwe (gemiddelde) dagprijzen voor stroom en gas toe
        sql_update_query_01 = """update config set PARAMETER='""" + stroom_prijs + """',LABEL='Verbruik tarief elektriciteit dal in euro.' where ID='1';"""
        sql_update_query_02 = """update config set PARAMETER='""" + stroom_prijs + """',LABEL='Verbruik tarief elektriciteit piek in euro.' where ID='2';"""
        sql_update_query_03 = """update config set PARAMETER='""" + stroom_prijs + """',LABEL='Geleverd tarief elektriciteit dal in euro.' where ID='3';"""
        sql_update_query_04 = """update config set PARAMETER='""" + stroom_prijs + """',LABEL='Geleverd tarief elektriciteit piek in euro.' where ID='4';"""
        sql_update_query_15 = """update config set PARAMETER='""" + gas_prijs + """',LABEL='Verbruik tarief gas in euro.' where ID='15';"""
        cursor.execute(sql_update_query_01)   # update de config.db database
        cursor.execute(sql_update_query_02)   # update de config.db database
        cursor.execute(sql_update_query_03)   # update de config.db database
        cursor.execute(sql_update_query_04)   # update de config.db database
        cursor.execute(sql_update_query_15)   # update de config.db database
        sqliteConnection.commit()             # Sla de database aanpassingen op
        sqliteConnection.close()              # Sluit de database
        print("~/p1mon/mnt/ramdisk/config.db geüpdatet met Energyzero prijzen.")
    except:
        print("Fout bij het updaten van ~/p1mon/mnt/ramdisk/config.db met de Energyzero prijzen.")
        exit()

    try:
        sqliteConnection    = sqlite3.connect("/p1mon/data/config.db")   # Verbind met config.db
        cursor              = sqliteConnection.cursor()
        # voeg de nieuwe (gemiddelde) dagprijzen voor stroom en gas toe
        sql_update_query_01 = """update config set PARAMETER='""" + stroom_prijs + """',LABEL='Verbruik tarief elektriciteit dal in euro.' where ID='1';"""
        sql_update_query_02 = """update config set PARAMETER='""" + stroom_prijs + """',LABEL='Verbruik tarief elektriciteit piek in euro.' where ID='2';"""
        sql_update_query_03 = """update config set PARAMETER='""" + stroom_prijs + """',LABEL='Geleverd tarief elektriciteit dal in euro.' where ID='3';"""
        sql_update_query_04 = """update config set PARAMETER='""" + stroom_prijs + """',LABEL='Geleverd tarief elektriciteit piek in euro.' where ID='4';"""
        sql_update_query_15 = """update config set PARAMETER='""" + gas_prijs + """',LABEL='Verbruik tarief gas in euro.' where ID='15';"""
        cursor.execute(sql_update_query_01)   # update de config.db database
        cursor.execute(sql_update_query_02)   # update de config.db database
        cursor.execute(sql_update_query_03)   # update de config.db database
        cursor.execute(sql_update_query_04)   # update de config.db database
        cursor.execute(sql_update_query_15)   # update de config.db database
        sqliteConnection.commit()             # Sla de database aanpassingen op
        sqliteConnection.close()              # Sluit de database
        print("~/p1mon/data/config.db geüpdatet met Energyzero prijzen.")
    except:
        print("Fout bij het updaten van ~/p1mon/data/config.db met de Energyzero prijzen.")
        exit()

try:
    update_config()
    # Datum vandaag in het juiste format voor later
    today = datetime.datetime.now().strftime("%d-%m-%Y - %H:%M:%S")
    print('Update Energyzero gelukt op : ' + today)
except:
    print('Er is een fout opgetreden bij het updaten de Energyzero prijzen.')
    exit() 
