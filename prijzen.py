import asyncio
import datetime
import subprocess
import time
import sqlite3
# Energyzero module : pip install energyzero
from energyzero import EnergyZero

wan_connected = False
# Check of internet bereikbaar is
while not wan_connected:
    try:
        ping_output = subprocess.check_output(['ping', '-4', '-c', '1', '-w', '2', '208.67.222.222'])
        if b'1 received' in ping_output:
            print()
            print('Internet bereikbaar !')
            print()
            break
        else:
            print('Fout, internet niet bereikbaar !')
            time.sleep(60)
    except subprocess.CalledProcessError as d:
        print(f'Ping request failed with error: Netwerk is onbereikbaar')
        print('Nieuwe poging over 60 seconden !')
        time.sleep(60)


async def main() -> None:
    async with EnergyZero() as client:
        today            = datetime.datetime.now().date()
        energy_today     = None
        gas_today        = None
        current_electric = None
        current_gas      = None

        # get energy and gas prices for today, when none go to date-1 and try again until result
        while energy_today is None or gas_today is None:
            try:
                while energy_today is None or gas_today is None:
                    try:
                        if energy_today is None:
                            energy_today = await client.energy_prices(start_date=today, end_date=today)
                            if energy_today.current_price is None:
                                current_electric = energy_today.average_price  # set default price here
                            else:
                                current_electric = energy_today.current_price

                        if gas_today is None:
                            gas_today = await client.gas_prices(start_date=today, end_date=today)
                            if gas_today.current_price is None:
                                current_gas = gas_today.average_price  # set default price here
                            else:
                                current_gas = gas_today.current_price
                    except Exception as e:
                        print('Error : fout bij ophalen Energyzero prijzen')
                        print(e.message, e.args)

                # print Energyzero electric price
                # print(current_electric)
                # print(f"Actuele stroom prijs    incl. BTW : {energy_today.current_price}")
                # print(f"Gemiddelde stroom prijs incl. BTW : {energy_today.average_price}")
                # print()
                # print Energyzero gas price
                # print(current_gas)
                # print()
                # print(f"Actuele gas prijs    incl. BTW : {gas_today.current_price}")
                # print(f"Gemiddelde gas prijs incl. BTW : {gas_today.average_price}")
                # print()
            except Exception as f:
                energy_today = None
                gas_today    = None
                today        = today - datetime.timedelta(days=1)
                print('Error : fout bij ophalen Energyzero prijzen')
                print(f.message, f.args)
                exit()

        try:
            replace_electric = round(current_electric + 0.17364, 5)     # add inkoopkosten, energiebelasting, ODE
            replace_solar    = round(current_electric, 5)               # ex inkoopkosten, energiebelasting, ODE
            replace_gas      = round(current_gas + 0.67541, 5)          # add inkoopkosten, energiebelasting, ODE
            set_price(replace_electric, replace_solar, replace_gas)
            print()
            print(' Energyzero prijzen -----------------')
            print()
            print(' Stroom prijs all inclusief : ' + str(replace_electric))
            print(' Prijs teruglevering        : ' + str(replace_solar))
            print(' Gas prijs all inclusief    : ' + str(replace_gas))
            print(' ------------------------------------')
        except Exception as g:
            print('Er is een fout opgetreden bij het updaten de Energyzero prijzen.')
            print(g)
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
        today = datetime.datetime.now().strftime("%d-%m-%Y - %H:%M:%S")
        print('Update Energyzero gelukt op : ' + today)
        print("Succes : config.db geüpdatet met Energyzero prijzen.")

    except Exception as h:
        print("Fout bij het updaten van ~/p1mon/mnt/ramdisk/config.db met de Energyzero prijzen.")
        print(h)


if __name__ == "__main__":
    asyncio.run(main())
