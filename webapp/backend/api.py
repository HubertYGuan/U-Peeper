from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    Response,
    Request,
    status,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import HTMLResponse
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
from enum import Enum

class WS_Type(Enum):
    MCU = 0
    REMOTE = 1

class CMD_Type(Enum):
    FORWARD = 0
    LEFT = 1
    RIGHT = 2
    BACK = 3
class U_WebSocket():    
    def __init__(self, websocket: WebSocket, ws_type: int):
        self.websocket = websocket
        self.ws_type = ws_type
        
# Currently only support for one mcu websocket (but it technically sends cmds to all at once)
class WS_Manager():
    def __init__(self):
        self.active_connections: list[U_WebSocket] = []
    async def connect(self, websocket: WebSocket, ws_type: int):
        U_websocket = U_WebSocket(websocket, ws_type)
        self.active_connections.append(U_websocket)

    def disconnect(self, websocket: WebSocket):
        for ele in self.active_connections:
            if ele.websocket.__repr__() == websocket.__repr__:
                self.active_connections.remove(ele)
    async def send_cmd(self, cmd: int):
        for ele in self.active_connections:
            if ele.ws_type == WS_Type.MCU:
                await ele.websocket.send_bytes(cmd)
    async def notify_remote(self, data: str):
        for ele in self.active_connections:
            if ele.ws_type == WS_Type.REMOTE:
                await ele.websocket.send_text(data)
                
app = FastAPI()

# singleton for managing all current WebSocket Connections
manager = WS_Manager()

async def find_event_type(event_type: str, db: AsyncSession):
    results = await db.execute(
        select(Event_Type).where(Event_Type.name == event_type).limit(1)
    )
    return results.scalars().first()


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
    
    timestamp = datetime.datetime.now()
    if raw_timestamp:
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


@app.websocket("/mcu/ws/")
async def mcu_websocket(websocket: WebSocket):
    await websocket.accept()
    await manager.connect(websocket, WS_Type.MCU)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"sending data: {data}")
            await manager.notify_remote(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.websocket("/remote/ws/")
async def remote_websocket(websocket: WebSocket):
    await websocket.accept()
    await manager.connect(websocket, WS_Type.REMOTE)
    try:
        while True:
            cmd = await websocket.receive_bytes()
            print(f"sending cmd: {cmd}")
            await manager.send_cmd(cmd)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
