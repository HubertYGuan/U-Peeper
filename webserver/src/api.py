from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    Response,
    Request,
    status,
    WebSocket,
)
from fastapi.responses import StreamingResponse
from typing import Annotated, Optional
from fastapi.security import HTTPBearer, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from sqlalchemy import select, update, delete, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from db_models.db_models import Event, Event_Type
from databaseinit import Get_DB
import time
import datetime
from dotenv import load_dotenv
import os


async def find_event_type(event_type: str, db: AsyncSession):
    results = await db.execute(
        select(Event_Type).where(Event_Type.name == event_type).limit(1)
    )
    return results.scalars().first()


app = FastAPI()


@app.get("/")
def root():
    return {"message": "Cool test json, also go to /docs to get the docs"}


# I don't feel like doing an auth system tbh
# So don't expose it to the open internet


@app.get("/events/read/")
async def read_events(db: AsyncSession = Depends(Get_DB)):
    results = await db.execute(select(Event).options(selectinload(Event.event_type)))
    events_list = results.scalars().all()
    return {"Driving events:": events_list}


@app.get("/events/read/{rowid}")
async def read_event(rowid: int, db: AsyncSession = Depends(Get_DB)):
    results = await db.execute(
        select(Event)
        .options(selectinload(Event.event_type))
        .where(Event.rowid == rowid)
    )
    events_list = results.scalars().first()
    return {f"Driving event {rowid}:": events_list}


@app.get("/event_types/read/")
async def read_event_types(db: AsyncSession = Depends(Get_DB)):
    results = await db.execute(
        select(Event_Type).options(selectinload(Event_Type.events))
    )
    event_types_list = results.scalars().all()
    return {"Event types:": event_types_list}


@app.get("/event_types/read/{rowid}")
async def read_event_type(rowid: int, db: AsyncSession = Depends(Get_DB)):
    results = await db.execute(
        select(Event_Type)
        .options(selectinload(Event_Type.events))
        .where(Event_Type.rowid == rowid)
    )
    events_types_list = results.scalars().first()
    return {f"Event type {rowid}:": events_types_list}


@app.put("/events/update/{rowid}")
async def update_event(
    rowid: int | None = None,
    description: str | None = None,
    raw_timestamp: str | None = None,
    event_type: str | None = None,
    db: AsyncSession = Depends(Get_DB),
):
    event_type_data = await find_event_type(event_type, db)
    timestamp = datetime.datetime.fromtimestamp(raw_timestamp)

    results = await db.execute(
        update(Event)
        .where(Event.rowid == rowid)
        .values(
            description=description,
            timestamp=timestamp,
            raw_timestamp=raw_timestamp,
            event_type=event_type_data,
        )
    )
    await db.commit()

    results = await db.execute(select(Event).where(Event.rowid == rowid).limit(1))
    return results.scalars().first()


@app.post("/events/add")
async def add_event(
    description: str | None = None,
    raw_timestamp: str | None = None,
    event_type: str | None = None,
    db: AsyncSession = Depends(Get_DB),
):
    event_type_data = await find_event_type(event_type, db)
    timestamp = datetime.datetime.fromtimestamp(raw_timestamp)

    results = await db.execute(
        insert(Event).values(
            description=description,
            timestamp=timestamp,
            raw_timestamp=raw_timestamp,
            event_type=event_type_data,
        )
    )
    await db.commit()

    results = await db.execute(select(Event).order_by(Event.rowid.desc).limit(1))
    return results.scalars().first()


@app.delete("/events/delete/{rowid}")
async def delete_event(rowid: int, db: AsyncSession = Depends(Get_DB)):
    await db.execute(delete(Event).where(Event.rowid == rowid))
    await db.commit()
    return {f"Driving event {rowid} deleted (probably)"}


@app.websocket("/ws/")
async def main_websocket(websocket: WebSocket):
    await websocket.accept()
    # Infinite loop bad
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
