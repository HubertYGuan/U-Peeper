## @file api.py
# @brief Main backend REST API
#
# Includes endpoints for adding events and event types (e.g. Ultrasonic events)
# See db_models/db_models.py for more info on events and event types
# Also includes two WebSocket endpoints for managing remote to microcontroller communication

from fastapi import (
    FastAPI,
    Depends,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from db_models.db_models import Event, Event_Type
from databaseinit import Get_DB
import datetime
from enum import Enum

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (definitely insecure)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


##
# @brief Types of WebSocket connections possible
class WS_Type(Enum):
    MCU = 0
    REMOTE = 1


##
# @brief Storage class that associates a WS_Type with a WebSocket connection
class U_WebSocket:
    def __init__(self, websocket: WebSocket, ws_type: int):
        self.websocket = websocket
        self.ws_type = ws_type


##
# @brief Manager class for WebSockets
#
# Currently only supports one mcu/remote websocket (sends cmds to opposite WebSockets at once)
class WS_Manager:
    ##
    # @brief Initialize with an empty list of U_WebSocket connections
    def __init__(self):
        self.active_connections: list[U_WebSocket] = []

    ##
    # @brief Connects a WebSocket
    async def connect(self, websocket: WebSocket, ws_type: int):
        U_websocket = U_WebSocket(websocket, ws_type)
        self.active_connections.append(U_websocket)

    ##
    # @brief Disconnects a WebSocket
    def disconnect(self, websocket: WebSocket):
        for ele in self.active_connections:
            if ele.websocket == websocket:
                print("removed websock connection in manager")
                self.active_connections.remove(ele)

    ##
    # @brief Broadcasts a command from a remote to all mcu WebSockets
    async def send_cmd(self, cmd):
        for ele in self.active_connections:
            if ele.ws_type == WS_Type.MCU:
                print(f"manager sending {cmd}")
                data = bytes(cmd)
                await ele.websocket.send_bytes(data)

    ##
    # @brief Broadcasts a notification from an mcu to all remote WebSockets
    async def notify_remote(self, data: str):
        for ele in self.active_connections:
            if ele.ws_type == WS_Type.REMOTE:
                await ele.websocket.send_text(data)


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


##
# @brief Gets all events
@app.get("/events/read/")
async def read_events(db: AsyncSession = Depends(Get_DB)):
    results = await db.execute(select(Event).options(selectinload(Event.event_type)))
    events_list = results.scalars().all()
    return {"Driving events:": events_list}


##
# @brief Gets event based on rowid
# @param rowid: ID of the event
@app.get("/events/read/{rowid}")
async def read_event(rowid: int, db: AsyncSession = Depends(Get_DB)):
    results = await db.execute(
        select(Event)
        .options(selectinload(Event.event_type))
        .where(Event.rowid == rowid)
    )
    events_list = results.scalars().first()
    return {f"Driving event {rowid}:": events_list}


##
# @brief Gets event_types
@app.get("/event_types/read/")
async def read_event_types(db: AsyncSession = Depends(Get_DB)):
    results = await db.execute(
        select(Event_Type).options(selectinload(Event_Type.events))
    )
    event_types_list = results.scalars().all()
    return {"Event types:": event_types_list}


##
# @brief Gets event_types based on rowid
# @param rowid: ID of the event_type
@app.get("/event_types/read/{rowid}")
async def read_event_type(rowid: int, db: AsyncSession = Depends(Get_DB)):
    results = await db.execute(
        select(Event_Type)
        .options(selectinload(Event_Type.events))
        .where(Event_Type.rowid == rowid)
    )
    events_types_list = results.scalars().first()
    return {f"Event type {rowid}:": events_types_list}


##
# @brief Inserts new event_type
# @param name: Name of the new event
@app.post("/event_types/add/")
async def add_event_type(name: str, db: AsyncSession = Depends(Get_DB)):
    new_event_type = Event_Type(name=name, events=[])
    db.add(new_event_type)
    await db.commit()

    results = await db.execute(
        select(Event_Type)
        .options(selectinload(Event_Type.events))
        .order_by(Event_Type.rowid.desc())
        .limit(1)
    )
    return results.scalars().first()


##
# @brief Gets all event_types
@app.get("/event_types/")
async def get_event_types(db: AsyncSession = Depends(Get_DB)):
    results = await db.execute(
        select(Event_Type).options(selectinload(Event_Type.events))
    )
    event_types_list = results.scalars().all()
    return {"Event types:": event_types_list}


##
# @brief Deletes an event type
# @param event_type_id: ID of the event type to delete
@app.delete("/event_types/{event_type_id}")
async def delete_event_type(event_type_id: int, db: AsyncSession = Depends(Get_DB)):
    await db.execute(delete(Event_Type).where(Event_Type.rowid == event_type_id))
    await db.commit()
    return {f"Driving event type {event_type_id} deleted (probably)"}


##
# @brief Updates an existing event
# @param rowid: ID of the event to update
# @param description: New description, default None
# @param raw_timestamp: Updated POSIX timestamp, default None
# @param event_type: Name of updated event_type, default None
# @return Updated event
@app.put("/events/update/{rowid}")
async def update_event(
    rowid: int,
    description: str | None = None,
    raw_timestamp: float | None = None,
    event_type: str | None = None,
    db: AsyncSession = Depends(Get_DB),
):
    event_type_data = await find_event_type(event_type, db)

    event = await db.get(Event, rowid)
    if description:
        event.description = description
    if raw_timestamp:
        event.raw_timestamp = raw_timestamp
        timestamp = datetime.datetime.fromtimestamp(raw_timestamp)
        event.timestamp = timestamp
    if event_type_data:
        event.event_type = event_type_data

    await db.commit()

    results = await db.execute(select(Event).where(Event.rowid == rowid).limit(1))
    return results.scalars().first()


##
# @brief Inserts an event
# @param description: New description, default "N/A"
# @param raw_timestamp: Updated POSIX timestamp, default current time
# @param event_type: Name of updated event_type, default "Turn On"
# @return New event
@app.post("/events/add")
async def add_event(
    description: str | None = "N/A",
    # I know this is actually the time when the server starts
    raw_timestamp: float | None = datetime.datetime.now().timestamp(),
    event_type: str | None = "Turn On",  # Turn on is the defaultly inserted event type
    db: AsyncSession = Depends(Get_DB),
):
    event_type_data = await find_event_type(event_type, db)
    timestamp = datetime.datetime.fromtimestamp(raw_timestamp)

    new_event = Event(
        description=description,
        raw_timestamp=raw_timestamp,
        timestamp=timestamp,
        event_type=event_type_data,
    )
    db.add(new_event)
    await db.commit()

    results = await db.execute(
        select(Event)
        .options(selectinload(Event.event_type))
        .order_by(Event.rowid.desc())
        .limit(1)
    )
    return results.scalars().first()


##
# @brief Deletes an event
# @param rowid: ID of event to delete
@app.delete("/events/delete/{rowid}")
async def delete_event(rowid: int, db: AsyncSession = Depends(Get_DB)):
    await db.execute(delete(Event).where(Event.rowid == rowid))
    await db.commit()
    return {f"Driving event {rowid} deleted (probably)"}


##
# @brief WebSocket endpoint for microcontrollers
#
# Automatically forwards data received from the mcu to the WS_Manager to notify remote
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


##
# @brief WebSocket endpoint for remotes
#
# Automatically forwards data received from the remote to the WS_Manager to send command
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
