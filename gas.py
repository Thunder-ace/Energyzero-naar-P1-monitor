import asyncio
import datetime
import pytz
from energyzero import EnergyZero

async def main() -> None:
    async with EnergyZero() as client:
        local        = pytz.timezone("Europe/Amsterdam")
        today        = datetime.datetime.now().date()
        gas_today    = None
        # get energy prices today, when none go to date-1 and try again until result
        while gas_today is None:
            try:
                gas_today      = await client.gas_prices(start_date=today, end_date=today)
                # print average price ex and incl.
                print(gas_today.average_price)
                print(round(gas_today.average_price + 0.67541, 2))
            except:
                gas_today = None
                today     = today - datetime.timedelta(days=1)
            pass

if __name__ == "__main__":
    asyncio.run(main())
