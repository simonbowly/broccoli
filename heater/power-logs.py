import asyncio
import logging
import time
from datetime import datetime, timezone

import asyncpg
from wemo.asyncio import get_insight_info

logger = logging.getLogger(__name__)


def repr_call(func, args, kwargs):
    result = func.__name__ + "("
    if args:
        result += ", ".join(args) + ", "
    if kwargs:
        result += ", ".join(f"{k}={v}" for k, v in kwargs.items())
    return result + ")"


async def read_forever(read, *args, delay_seconds, **kwargs):
    logger.info(f"Starting read loop for {repr_call(read, args, kwargs)}")
    while True:
        await asyncio.sleep(delay_seconds - (time.time() % delay_seconds))
        result = await read(*args, **kwargs)
        result["time"] = datetime.now(tz=timezone.utc)
        logger.info(f"Read measurement at {result['time']}")
        yield result


from typing import List


async def insert_measurement(connection, table: str, fields: List[str], measurement):
    values = ", ".join(f"${i+1}" for i, _ in enumerate(fields))
    statement = f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({values})"
    await connection.execute(statement, *(measurement[field] for field in fields))


async def main():
    connection = await asyncpg.connect("postgresql://pi:123@localhost/broccoli")
    wemo_state_names = {
        row['name']: row['id']
        for row in await connection.fetch("SELECT id, name FROM wemo_states")
    }
    try:
        async for measurement in read_forever(
            get_insight_info, "10.1.1.4", delay_seconds=3
        ):
            measurement['state_id'] = wemo_state_names[measurement['state']]
            await insert_measurement(
                connection,
                table="wemo_records",
                measurement=measurement,
                fields=[
                    "state_id",
                    "current_power_mw",
                    "last_state_change",
                    "on_for_seconds",
                    "on_today_seconds",
                    "on_total_seconds",
                    "power_threshold_mw",
                    "time",
                    "time_period",
                    "today_mw",
                    "total_mw",
                    "unknown",
                ],
            )
            logger.info(f"Wrote measurement at {datetime.now(tz=timezone.utc)}")
    finally:
        await connection.close()


logging.basicConfig(level=logging.INFO)
asyncio.run(main())
