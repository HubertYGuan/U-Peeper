from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, ForeignKeyConstraint
from typing import List


class DB_Base(DeclarativeBase):
    pass


class Event_Type(DB_Base):
    __tablename__ = "event_types"
    name: Mapped[str] = mapped_column(nullable=False)
    events: Mapped[List["Event"]] = relationship(back_populates="event_type")
    rowid: Mapped[int] = mapped_column(primary_key=True)


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
