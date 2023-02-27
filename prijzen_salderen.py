# Addon to use dynamic energy prices for the P1-Monitor software from ztatz.nl with code for a kind of ""salderen"
#
# setup as prijzen.py only crontab needs to be updated :
# 5 * * * * /usr/bin/python3 /p1mon/scripts/prijzen_salderen.py >> /p1mon/var/tmp/update_prijzen_$(date +\%Y\%m\%d\%H\%M\%S).log 2>&1; ls -t /p1mon/var/tmp    /update_prijzen_*.log | tail -n +25 | xargs rm -f # Energyzero_Update
#
# History:
# 1.0.0   27-02-2023  Initial version


"""
Copyright (c) 2023 by R.C.Bleeker

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import asyncio
import datetime
import socket
import time
import sqlite3
from energyzero import EnergyZero


def validate_connection(host: str) -> bool:
    try:
        # Perform DNS lookup to get IP address
        ip_addresses = socket.gethostbyname_ex(host.strip())[-1]
        if ip_addresses:
            # Try to connect to port (e.g. 53 for DNS)
            for ip_address in ip_addresses:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1.0)
                    result = sock.connect_ex((ip_address, 53))
                    if result == 0:
                        # Connection success, so internet is reachable
                        check_timestamp = datetime.datetime.now().strftime("%d-%m-%Y - %H:%M:%S")
                        print("----------------------------------------------------------------------")
                        print(f"{check_timestamp} : Internet verbinding actief !")
                        return True
        # If no connections, internet is not reachable
        check_timestamp = datetime.datetime.now().strftime("%d-%m-%Y - %H:%M:%S")
        print("----------------------------------------------------------------------")
        print(f"{check_timestamp} : Geen internet verbinding!")
    except socket.gaierror:
        check_timestamp = datetime.datetime.now().strftime("%d-%m-%Y - %H:%M:%S")
        print("----------------------------------------------------------------------")
        print(f"{check_timestamp} : Geen internet verbinding !")
        print("Error : Hostname could not be resolved, so assume internet is not reachable.")
    except socket.timeout:
        check_timestamp = datetime.datetime.now().strftime("%d-%m-%Y - %H:%M:%S")
        print("----------------------------------------------------------------------")
        print(f"{check_timestamp} : Geen internet verbinding !")
        print("Error : Connection timed out, so assume internet is not reachable")
    except Exception as e:
        check_timestamp = datetime.datetime.now().strftime("%d-%m-%Y - %H:%M:%S")
        print("----------------------------------------------------------------------")
        print(f"{check_timestamp} : Geen internet verbinding !")
        print(f"Error : {e}")
    return False

# ----------------------------------------------------------------------------------------------------------------------
# Check for internet connection.
# If no internet retry 5 times with a 60 seconds interval.
# Exit and NO updates when there is no internet connection.
# ----------------------------------------------------------------------------------------------------------------------


MAX_ATTEMPTS = 5
attempts     = 0
while not validate_connection("one.one.one.one") and attempts < MAX_ATTEMPTS:
    attempts += 1
    if attempts < MAX_ATTEMPTS:
        print(f"Nieuwe poging over 60 seconden (poging {attempts} van {MAX_ATTEMPTS})")
        time.sleep(2)
    else:
        check_wan = datetime.datetime.now().strftime("%d-%m-%Y - %H:%M:%S")
        print("----------------------------------------------------------------------")
        print(f"Internet niet bereikbaar na {MAX_ATTEMPTS} pogingen.")
        print("Ophalen actuele Energyzero prijzen voor stroom en gas gestopt.")
        print("Er zijn GEEN Energyzero updates verwerkt.")
        print("----------------------------------------------------------------------")
        print(f"Volgend uur wordt een nieuwe poging gedaan voor de Energyzero update.")
        print("----------------------------------------------------------------------")
        exit()

# ----------------------------------------------------------------------------------------------------------------------
# Internet connected so proceed.
# ----------------------------------------------------------------------------------------------------------------------


def calculate_energy_totals(date):
    """
    Calculate the energy totals for a given date.
    """
    # initialize energy totals to zero
    total_consumption = 0
    total_production  = 0
    total_export      = 0
    total_import      = 0

    # connect to the e_history.db database using a context manager
    with sqlite3.connect('/p1mon/data/e_historie.db') as conn:
        # create a cursor object
        c = conn.cursor()

        # execute a parameterized SQL query to fetch energy data for the given date
        query = "SELECT VERBR_KWH_181, VERBR_KWH_182, GELVR_KWH_281, GELVR_KWH_282 FROM e_history_dag WHERE TIMESTAMP LIKE ? LIMIT 1;"
        c.execute(query, (f"{date}%",))

        # fetch the results and extract the energy values
        result = c.fetchone()
        start_181, start_182, start_281, start_282 = result

        # execute another query to fetch energy data for today's date
        query = "SELECT VERBR_KWH_181, VERBR_KWH_182, GELVR_KWH_281, GELVR_KWH_282 FROM e_history_dag WHERE TIMESTAMP LIKE ? LIMIT 1;"
        c.execute(query, (f"{datetime.date.today()}%",))

        # fetch the results and extract the energy values
        result = c.fetchone()
        today_181, today_182, today_281, today_282 = result

        # calculate energy totals
        total_consumption = round(today_181 - start_181 + today_182 - start_182, 2)
        total_production = round(today_281 - start_281 + today_282 - start_282, 2)
        total_export = round(max(0, total_production - total_consumption), 2)
        total_import = round(max(0, total_consumption - total_production), 2)

        # close the cursor (the connection is automatically closed by the context manager)
        c.close()

    # return the energy totals as a tuple
    return (total_consumption, total_production, total_export, total_import)


async def main() -> None:
    async with EnergyZero() as client:
        date_contract      = '2023-01-17'  # <==== make it you're own start date !!!
        today              = datetime.datetime.now().date()
        energy_today       = None
        gas_today          = None
        current_electric   = None           # electricity price incl. VAT
        inkoopkosten_e     = 0.02118        # electricity surcharges    (change if needed)
        energiebelasting_e = 0.15246        # electricity surcharges    (change if needed)
        ode_e              = 0.00           # electricity surcharges    (change if needed)
        current_gas        = None           # gas price incl. VAT
        inkoopkosten_g     = 0.08275        # gas surcharges            (change if needed)
        energiebelasting_g = 0.59266        # gas surcharges            (change if needed)
        ode_g              = 0.00           # gas surcharges            (change if needed)
        # --------------------------------------------------------------------------------------------------------------
        # get actual price(s) for electricity
        # --------------------------------------------------------------------------------------------------------------
        try:
            energy_today = await client.energy_prices(start_date=today, end_date=today)
            if energy_today is None or not energy_today.current_price:
                print("Geen actueel Energyzero stroom tarief gevonden.")
                print("Energyzero stroom tarief in P1-Monitor niet aangepast.")
            else:
                # ------------------------------------------------------------------------------------------------------
                # Set Energyzero current price electric
                # ------------------------------------------------------------------------------------------------------
                current_electric = energy_today.current_price
                replace_electric = round(current_electric + inkoopkosten_e + energiebelasting_e + ode_e, 5)
                replace_solar    = round(current_electric, 5)
                print('----------------------------------------------------------------------')
                print(f'Stroom prijs                                          : € {current_electric}')
                print(f'Inkoopkosten                                          : € {inkoopkosten_e}')
                print(f'Energiebelasting                                      : € {energiebelasting_e}')
                print(f'ODE                                                   : € {ode_e}')
                print(f'Stroom prijs inclusief                                : € {replace_electric}')
                # ------------------------------------------------------------------------------------------------------
                # Make a calculation to see if the electricity production is higher then the consumption or not : salderen
                # ------------------------------------------------------------------------------------------------------

                try:
                    total_consumption_1, total_production_1, total_export_1, total_import_1 = calculate_energy_totals(date_contract)
                    total_consumption_2, total_production_2, total_export_2, total_import_2 = calculate_energy_totals(datetime.datetime.now().date())
                    if total_consumption_1 >= total_production_1:
                        replace_solar = replace_electric
                        print('----------------------------------------------------------------------')
                        print(f'Prijs teruglevering (salderen actief)                : € {replace_solar} ')
                        print('----------------------------------------------------------------------')
                    else:
                        replace_solar = current_electric
                        print('----------------------------------------------------------------------')
                        print(f'Prijs teruglevering (salderen niet actief)           : € {replace_solar} ')
                        print('----------------------------------------------------------------------')
                except:
                    # on error use standard price for electricity.
                    print('----------------------------------------------------------------------')
                    print(f'Prijs teruglevering (fout bij berekenen salderen)    : € {replace_solar} ')
                    print('----------------------------------------------------------------------')

                # ------------------------------------------------------------------------------------------------------
                # Update config.db in /p1mon/mnt/ramdisk/
                # ------------------------------------------------------------------------------------------------------

                with sqlite3.connect("/p1mon/mnt/ramdisk/config.db") as sqlite_connection:
                    cursor = sqlite_connection.cursor()
                    for id, value in [(1, replace_electric), (2, replace_electric), (3, replace_solar), (4, replace_solar)]:
                        sql_update_query = """UPDATE config SET PARAMETER='{}' WHERE ID='{}';""".format(str(value), str(id))
                        cursor.execute(sql_update_query)
                        sqlite_connection.commit()

                print('Energyzero stroom /p1mon/mnt/ramdisk/config.db update : Succes !')

                # ------------------------------------------------------------------------------------------------------
                #  Update config.db in /p1mon/data/
                #  code for update in config.db is not needed, comment from ztatz.nl :
                #  "This is not necessary because the data from the RAM database is automatically copied by
                #  the P1 software." Thanks to Security Brother / ztatz.nl
                # ------------------------------------------------------------------------------------------------------

        except Exception as e_stroom:
            print()
            print("! Fout bij het updaten van config.db met de Energyzero stroom prijs.")
            print(f"! Systeem foutmelding : {e_stroom}")
            print()

        # --------------------------------------------------------------------------------------------------------------
        # get actual price(s) for gas
        # --------------------------------------------------------------------------------------------------------------
        try:
            gas_today = await client.gas_prices(start_date=today, end_date=today)
            if gas_today is None or not gas_today.current_price:
                print("Geen actueel Energyzero gas tarief gevonden.")
                print("Energyzero gas tarief in P1-Monitor niet aangepast.")
            else:
                # ------------------------------------------------------------------------------------------------------
                # Set Energyzero current price electric
                # ------------------------------------------------------------------------------------------------------
                current_gas = gas_today.current_price
                replace_gas = round(current_gas + inkoopkosten_g + energiebelasting_g + ode_g, 5)
                print('----------------------------------------------------------------------')
                print(f'Gas prijs                                             : € {current_gas}')
                print(f'Inkoopkosten                                          : € {inkoopkosten_g}')
                print(f'Energiebelasting                                      : € {energiebelasting_g}')
                print(f'ODE                                                   : € {ode_g}')
                print(f'Gas prijs inclusief                                   : € {replace_gas}')
                print('----------------------------------------------------------------------')

                # Update config.db in /p1mon/mnt/ramdisk/
                with sqlite3.connect("/p1mon/mnt/ramdisk/config.db") as sqlite_connection:
                    cursor = sqlite_connection.cursor()
                    sql_update_query_15 = """UPDATE config SET PARAMETER='{}' WHERE ID='15';""".format(str(replace_gas))
                    cursor.execute(sql_update_query_15)
                    sqlite_connection.commit()

                print('Energyzero gas /p1mon/mnt/ramdisk/config.db update    : Succes !')

                # ------------------------------------------------------------------------------------------------------
                #  Update config.db in /p1mon/data/
                #  code for update in config.db is not needed, comment from ztatz.nl :
                #  "This is not necessary because the data from the RAM database is automatically copied by
                #   the P1 software." Thanks to Security Brother / ztatz.nl
                # ------------------------------------------------------------------------------------------------------

        except Exception as e_gas:
            print()
            print("! Fout bij het updaten van config.db met de Energyzero gas prijs.")
            print(f"! Systeem foutmelding : {e_gas}")
            print()

if __name__ == "__main__":
    asyncio.run(main())
