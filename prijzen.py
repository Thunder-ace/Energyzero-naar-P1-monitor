import asyncio
import datetime
import socket
import time
import sqlite3
# Energyzero module : pip install energyzero
from energyzero import EnergyZero


def validateconnection(host: str):
    try:
        dnslookup: tuple = socket.gethostbyname_ex(host.strip())
        if dnslookup[-1]:
            ipaddress: str = dnslookup[-1][0]
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1.0)
                result: int = sock.connect_ex((ipaddress, 53))
                if result == 0:
                    check_timestamp = datetime.datetime.now().strftime("%d-%m-%Y - %H:%M:%S")
                    print("----------------------------------------------------------------------")
                    print(f"{check_timestamp} : Internet verbinding !")
                    return True
    except:
        check_timestamp = datetime.datetime.now().strftime("%d-%m-%Y - %H:%M:%S")
        print("----------------------------------------------------------------------")
        print(f"{check_timestamp} : Geen internet verbinding !")
    return False

# ----------------------------------------------------------------------------------------------------------------------
# Check for internet connection.
# If no internet retry 5 times with a 60 seconds interval.
# Exit and NO updates when there is no internet connection.
# ----------------------------------------------------------------------------------------------------------------------
MAX_ATTEMPTS = 5
attempts = 0
while not validateconnection("one.one.one.one") and attempts < MAX_ATTEMPTS:
    attempts += 1
    if attempts < MAX_ATTEMPTS:
        print(f"Nieuwe poging over 60 seconden (poging {attempts} van {MAX_ATTEMPTS})")
        time.sleep(5)
    else:
        check_wan = datetime.datetime.now().strftime("%d-%m-%Y - %H:%M:%S")
        print("----------------------------------------------------------------------")
        print(f"Internet niet bereikbaar na {MAX_ATTEMPTS} pogingen.")
        print("Ophalen actuele Energyzero prijzen voor stroom en gas gestopt.")
        print("Er zijn GEEN Energyzero updates verwerkt.")
        # Get the current time for calculation when next attempt for update
        check_wan = datetime.datetime.now()
        # Round down to the nearest whole hour
        check_wan = check_wan.replace(minute=0, second=0, microsecond=0)
        # Round up to the next hour
        if check_wan.minute >= 1:
            next_hour = check_wan.replace(hour=check_wan.hour + 1)
        else:
            next_hour = check_wan
        # Check if next_hour is on the next day
        if next_hour.day > check_wan.day:
            next_hour = next_hour.replace(hour=0)
        # Add the necessary time to the datetime object
        check_wan_with_time = next_hour + datetime.timedelta(minutes=5)
        # Format the datetime object as a string
        check_wan_with_time_str = check_wan_with_time.strftime("%d-%m-%Y %H:%M:%S")
        print("----------------------------------------------------------------------")
        print(f"Volgende poging Energyzero update : {check_wan_with_time_str}")
        print("----------------------------------------------------------------------")
        exit()

# ----------------------------------------------------------------------------------------------------------------------
# Internet connected so proceed.
# ----------------------------------------------------------------------------------------------------------------------
async def main() -> None:
    async with EnergyZero() as client:
        today              = datetime.datetime.now().date()
        energy_today       = None
        gas_today          = None
        current_electric   = None           # electricity price incl. VAT
        inkoopkosten_e     = 0.02118        # electricity surcharges (change if needed)
        energiebelasting_e = 0.15246        # gas surcharges (change if needed)
        ode_e              = 0.00           # gas surcharges (change if needed)
        current_gas        = None           # gas price inl. VAT
        inkoopkosten_g     = 0.08275        # gas surcharges (change if needed)
        energiebelasting_g = 0.59266        # gas surcharges (change if needed)
        ode_g              = 0.00           # gas surcharges (change if needed)
        # --------------------------------------------------------------------------------------------------------------
        # get actual price(s) for electricity
        # --------------------------------------------------------------------------------------------------------------
        try:
            energy_today = await client.energy_prices(start_date=today, end_date=today)
            if energy_today is None or not energy_today.current_price:
                print('Fout: Geen actuele Energyzero stroom prijs gevonden.')
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
                print('----------------------------------------------------------------------')
                print(f'Prijs teruglevering                                   : € {current_electric} ')
                print('----------------------------------------------------------------------')
                # Update config.db in /p1mon/mnt/ramdisk/
                with sqlite3.connect("/p1mon/mnt/ramdisk/config.db") as sqlite_connection:
                    cursor = sqlite_connection.cursor()
                    sql_update_query_01 = """update config set PARAMETER='""" + str(
                        replace_electric) + """',LABEL='Verbruik tarief elektriciteit dal in euro.' where ID='1';"""
                    sql_update_query_02 = """update config set PARAMETER='""" + str(
                        replace_electric) + """',LABEL='Verbruik tarief elektriciteit piek in euro.' where ID='2';"""
                    sql_update_query_03 = """update config set PARAMETER='""" + str(
                        replace_solar) + """',LABEL='Geleverd tarief elektriciteit dal in euro.' where ID='3';"""
                    sql_update_query_04 = """update config set PARAMETER='""" + str(
                        replace_solar) + """',LABEL='Geleverd tarief elektriciteit piek in euro.' where ID='4';"""
                    cursor.execute(sql_update_query_01)
                    cursor.execute(sql_update_query_02)
                    cursor.execute(sql_update_query_03)
                    cursor.execute(sql_update_query_04)
                    sqlite_connection.commit()
                    print('Energyzero stroom /p1mon/mnt/ramdisk/config.db update : Succes !')

                # Update config.db in /p1mon/data/
                with sqlite3.connect("/p1mon/data/config.db") as sqlite_connection:
                    cursor = sqlite_connection.cursor()
                    sql_update_query_01 = """update config set PARAMETER='""" + str(
                        replace_electric) + """',LABEL='Verbruik tarief elektriciteit dal in euro.' where ID='1';"""
                    sql_update_query_02 = """update config set PARAMETER='""" + str(
                        replace_electric) + """',LABEL='Verbruik tarief elektriciteit piek in euro.' where ID='2';"""
                    sql_update_query_03 = """update config set PARAMETER='""" + str(
                        replace_solar) + """',LABEL='Geleverd tarief elektriciteit dal in euro.' where ID='3';"""
                    sql_update_query_04 = """update config set PARAMETER='""" + str(
                        replace_solar) + """',LABEL='Geleverd tarief elektriciteit piek in euro.' where ID='4';"""
                    cursor.execute(sql_update_query_01)
                    cursor.execute(sql_update_query_02)
                    cursor.execute(sql_update_query_03)
                    cursor.execute(sql_update_query_04)
                    sqlite_connection.commit()
                    print('Energyzero stroom /p1mon/data/config.db update        : Succes !')
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
                print('Fout: Geen actuele Energyzero gas prijs gevonden.')
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
                    sql_update_query_15 = """update config set PARAMETER='""" + str(replace_gas) + """',LABEL='Verbruik tarief gas in euro.' where ID='15';"""
                    cursor.execute(sql_update_query_15)
                    sqlite_connection.commit()
                    print('Energyzero gas /p1mon/mnt/ramdisk/config.db update    : Succes !')

                # Update config.db in /p1mon/data/
                with sqlite3.connect("/p1mon/data/config.db") as sqlite_connection:
                    cursor = sqlite_connection.cursor()
                    sql_update_query_15 = """update config set PARAMETER='""" + str(replace_gas) + """',LABEL='Verbruik tarief gas in euro.' where ID='15';"""
                    cursor.execute(sql_update_query_15)
                    sqlite_connection.commit()
                    print('Energyzero gas /p1mon/data/config.db update           : Succes !')
        except Exception as e_gas:
            print()
            print("! Fout bij het updaten van config.db met de Energyzero gas prijs.")
            print(f"! Systeem foutmelding : {e_gas}")
            print()


if __name__ == "__main__":
    asyncio.run(main())
