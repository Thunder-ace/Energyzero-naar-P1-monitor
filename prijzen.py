import asyncio
import datetime
import subprocess
import time
import sqlite3
# Energyzero module : pip install energyzero
from energyzero import EnergyZero


wan_connected = False
MAX_ATTEMPTS  = 5
attempts      = 0
# Check for internet connection, if not found retry 5 times after a wait for 60 seconds : no change when no connection.
while not wan_connected and attempts < MAX_ATTEMPTS:
    try:
        ping_output = subprocess.check_output(['ping', '-4', '-c', '1', '-w', '2', '208.67.222.222'])
        if b'1 received' in ping_output:
            print('----------------------------------------------------------------------')
            print('Internet bereikbaar.')
            print('----------------------------------------------------------------------')
            wan_connected = True
        else:
            attempts += 1
            if attempts < MAX_ATTEMPTS:
                print(f'Nieuwe poging over 60 seconden (poging {attempts} van {MAX_ATTEMPTS})')
                time.sleep(60)
    except subprocess.CalledProcessError as d:
        print('----------------------------------------------------------------------')
        print('Internet niet bereikbaar !')
        attempts += 1
        if attempts < MAX_ATTEMPTS:
            print(f'Nieuwe poging over 60 seconden (poging : {attempts} van {MAX_ATTEMPTS})')
            time.sleep(60)
        else:
            check_wan = datetime.datetime.now().strftime("%d-%m-%Y - %H:%M:%S")
            print('----------------------------------------------------------------------')
            print(f'Datum en tijd : {check_wan}')
            print(f'Energyzero api via internet niet bereikbaar, aantal pogingen {MAX_ATTEMPTS}.')
            print('Geen wijzigingen van de actuele Energyzero prijzen voor stroom en gas.')
            print('----------------------------------------------------------------------')
            exit()


async def main() -> None:
    async with EnergyZero() as client:
        today              = datetime.datetime.now().date()
        energy_today       = None
        gas_today          = None
        # electricity price
        current_electric   = None
        # electricity surcharges (change if needed)
        inkoopkosten_e     = 0.02118
        energiebelasting_e = 0.15246
        ode_e              = 0.00
        # gas price
        current_gas        = None
        # gas surcharges (change if needed)
        inkoopkosten_g     = 0.08275
        energiebelasting_g = 0.59266
        ode_g              = 0.00

        # get actual price(s) for electricity, when none found quite update
        try:
            energy_today = await client.energy_prices(start_date=today, end_date=today)
            if energy_today is None or energy_today.current_price is None:
                print('Geen actuele prijs voor Energyzero stroom gevonden.')
                print('Geen updates voor Energyzero stroom verwerkt.')
                exit()  # or raise an exception
            else:
                # Set Energyzero current price electric
                current_electric = energy_today.current_price
                # print('----------------------------------------------------------------------')
                # print(f'Actuele stroom prijs    incl. BTW : € {current_electric}')
                # print(f'Gemiddelde stroom prijs incl. BTW : € {energy_today.average_price}')
                # print('----------------------------------------------------------------------')
        except Exception as e_stroom:
            print('Er is een fout opgetreden bij het ophalen van Energyzero prijs voor stroom.')
            print(f'Details :', e_stroom)
            exit()

        # get actual price(s) for gas, when none found quite update
        try:
            gas_today = await client.gas_prices(start_date=today, end_date=today)
            if gas_today is None or gas_today.current_price is None:
                print('Geen actuele prijs voor Energyzero gas gevonden.')
                print('Geen updates voor Energyzero gas verwerkt.')
                exit()  # or raise an exception
            else:
                # Set Energyzero current price electric
                current_gas = gas_today.current_price
                # print(f'Actuele gas prijs    incl. BTW    : € {current_gas}')
                # print(f'Gemiddelde gas prijs incl. BTW    : € {gas_today.average_price}')
                # print('----------------------------------------------------------------------')
        except Exception as e_gas:
            print('Er is een fout opgetreden bij het ophalen van Energyzero prijs voor gas.')
            print(f'Details :', e_gas)
            exit()


    try:
        replace_electric = round(current_electric + inkoopkosten_e + energiebelasting_e + ode_e, 5)
        replace_solar    = round(current_electric, 5)
        replace_gas      = round(current_gas + inkoopkosten_g + energiebelasting_g + ode_g, 5)
        set_price(replace_electric, replace_solar, replace_gas)
        print(f'Stroom prijs                               : € {current_electric}')
        print(f'Inkoopkosten                               : € {inkoopkosten_e}')
        print(f'Energiebelasting                           : € {energiebelasting_e}')
        print(f'ODE                                        : € {ode_e}')
        print(f'Stroom prijs inclusief                     : € {replace_electric}')
        print('----------------------------------------------------------------------')
        print(f'Prijs teruglevering                        : € {current_electric} ')
        print('----------------------------------------------------------------------')
        print(f'Gas prijs                                  : € {current_gas}')
        print(f'Inkoopkosten                               : € {inkoopkosten_g}')
        print(f'Energiebelasting                           : € {energiebelasting_g}')
        print(f'ODE                                        : € {ode_g}')
        print(f'Gas prijs inclusief                        : € {replace_gas}')
        print('----------------------------------------------------------------------')
    except Exception as g_stroom:
        print()
        print('Er is een fout opgetreden bij het updaten de Energyzero prijzen.')
        print(f'Details :', g_stroom)
        exit()


def set_price(replace_electric, replace_solar, replace_gas):
    # Update /p1mon/mnt/ramdisk/config.db with actual Energyzero prices
    try:
        sqlite_connection = sqlite3.connect("/p1mon/mnt/ramdisk/config.db")  # connect with config.db
        cursor           = sqlite_connection.cursor()
        # update the old prices with the new Energyzero prices
        sql_update_query_01 = """update config set PARAMETER='""" + str(replace_electric) + """',LABEL='Verbruik tarief 
        elektriciteit dal in euro.' where ID='1';"""
        sql_update_query_02 = """update config set PARAMETER='""" + str(replace_electric) + """',LABEL='Verbruik tarief 
        elektriciteit piek in euro.' where ID='2';"""
        sql_update_query_03 = """update config set PARAMETER='""" + str(replace_solar) + """',LABEL='Geleverd tarief 
        elektriciteit dal in euro.' where ID='3';"""
        sql_update_query_04 = """update config set PARAMETER='""" + str(replace_solar) + """',LABEL='Geleverd tarief 
        elektriciteit piek in euro.' where ID='4';"""
        sql_update_query_15 = """update config set PARAMETER='""" + str(replace_gas) + """',LABEL='Verbruik tarief 
        gas in euro.' where ID='15';"""
        cursor.execute(sql_update_query_01)  # update de config.db database
        cursor.execute(sql_update_query_02)  # update de config.db database
        cursor.execute(sql_update_query_03)  # update de config.db database
        cursor.execute(sql_update_query_04)  # update de config.db database
        cursor.execute(sql_update_query_15)  # update de config.db database
        sqlite_connection.commit()           # Sla de database aanpassingen op
        sqlite_connection.close()            # Sluit de database
    except Exception as h:
        print("Fout bij het updaten van /p1mon/mnt/ramdisk/config.db met de Energyzero prijzen.")
        print(h)

    try:
        sqlite_connection = sqlite3.connect("/p1mon/data/config.db")  # connect with config.db
        cursor           = sqlite_connection.cursor()
        # update the old prices with the new Energyzero prices
        sql_update_query_01 = """update config set PARAMETER='""" + str(replace_electric) + """',LABEL='Verbruik tarief 
        elektriciteit dal in euro.' where ID='1';"""
        sql_update_query_02 = """update config set PARAMETER='""" + str(replace_electric) + """',LABEL='Verbruik tarief 
        elektriciteit piek in euro.' where ID='2';"""
        sql_update_query_03 = """update config set PARAMETER='""" + str(replace_solar) + """',LABEL='Geleverd tarief 
        elektriciteit dal in euro.' where ID='3';"""
        sql_update_query_04 = """update config set PARAMETER='""" + str(replace_solar) + """',LABEL='Geleverd tarief 
        elektriciteit piek in euro.' where ID='4';"""
        sql_update_query_15 = """update config set PARAMETER='""" + str(replace_gas) + """',LABEL='Verbruik tarief 
        gas in euro.' where ID='15';"""
        cursor.execute(sql_update_query_01)  # update de config.db database
        cursor.execute(sql_update_query_02)  # update de config.db database
        cursor.execute(sql_update_query_03)  # update de config.db database
        cursor.execute(sql_update_query_04)  # update de config.db database
        cursor.execute(sql_update_query_15)  # update de config.db database
        sqlite_connection.commit()           # Sla de database aanpassingen op
        sqlite_connection.close()            # Sluit de database

        today = datetime.datetime.now().strftime("%d-%m-%Y - %H:%M:%S")
        print('Update Energyzero gelukt op                : ' + today)
        print("Config.db geüpdatet met Energyzero prijzen : Succes .")
        print('----------------------------------------------------------------------')

    except Exception as i:
        print("Fout bij het updaten van /p1mon/data/config.db met de Energyzero prijzen.")
        print(i)


if __name__ == "__main__":
    asyncio.run(main())
