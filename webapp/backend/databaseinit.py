##
# @file databaseinit.py
# @brief File to initiate SQLite db connections

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from db_models.db_models import DB_Base, Event_Type, Event
import asyncio

from datetime import datetime


# For some reason trying to connect to :///db/database.sqlite3 will raise errors only if run from src/
DB_engine = create_async_engine(
    "sqlite+aiosqlite:////var/lib/db_data/database.sqlite3",
    connect_args={"check_same_thread": False},
)

DB_Session = async_sessionmaker(DB_engine)

##
# @brief Obtain AsyncSession of database
async def Get_DB():
    async with DB_engine.begin() as conn:
        await conn.run_sync(DB_Base.metadata.create_all)
        db = DB_Session()
    try:
        yield db
    finally:
        await db.close()


async def Drop_Tables():
    async with DB_engine.begin() as conn:
        await conn.run_sync(DB_Base.metadata.drop_all)


async def Create_Tables():
    async with DB_engine.begin() as conn:
        await conn.run_sync(DB_Base.metadata.create_all)


# TODO: Change this to insert the actual default event_types (tbd) (and possibly an init event)
async def Insert_Default():
    session = DB_Session()
    turn_on = Event_Type(
        name="Turn On",
        events=[
            Event(
                timestamp=datetime.now().isoformat(),
                raw_timestamp=datetime.now().timestamp(),
                description="Test Event",
            ),
        ],
    )
    session.add_all([turn_on])
    await session.commit()


def main():
    # Remove below if you want data to persist
    asyncio.run(Drop_Tables())
    asyncio.run(Create_Tables())
    # Insert some default table entries
    asyncio.run(Insert_Default())


if __name__ == "__main__":
    main()
