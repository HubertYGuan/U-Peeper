##
# @file db_models.py
# @brief Contains database models for events and event_types

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from typing import List


class DB_Base(DeclarativeBase):
    pass

##
# @brief Event type with name and backpopulated events
class Event_Type(DB_Base):
    __tablename__ = "event_types"
    name: Mapped[str] = mapped_column(nullable=False)
    events: Mapped[List["Event"]] = relationship(back_populates="event_type")
    rowid: Mapped[int] = mapped_column(primary_key=True)

##
# @brief Event with (raw) timestamp, description and backpopulated event_type
#
# Includes foreign key mapping to an event_type
class Event(DB_Base):
    __tablename__ = "events"
    timestamp: Mapped[str] = mapped_column(nullable=False)
    raw_timestamp: Mapped[float] = mapped_column(nullable=False)
    description: Mapped[str]
    event_type: Mapped["Event_Type"] = relationship(back_populates="events")
    rowid: Mapped[int] = mapped_column(primary_key=True)
    type_id: Mapped[int] = mapped_column(ForeignKey("event_types.rowid"))

    def __repr__(self) -> str:
        return f"Event at {self.timestamp} of type {self.event_type.name} with description: {self.description}"
