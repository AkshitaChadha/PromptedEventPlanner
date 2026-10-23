from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_name: Mapped[str] = mapped_column(String(160), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    guest_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_budget: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    preferred_theme: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    user_preferences: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    must_have_arrangements: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    things_to_avoid: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    budget_priorities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    dietary_requirements: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    accessibility_requirements: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="event", cascade="all, delete-orphan", order_by="Task.id"
    )
    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="event", cascade="all, delete-orphan", order_by="Expense.spent_on, Expense.id"
    )


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (UniqueConstraint("event_id", "template_key", name="uq_task_event_template"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    template_key: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    system_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    user_edited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    event: Mapped[Event] = relationship(back_populates="tasks")


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    spent_on: Mapped[date] = mapped_column(Date, nullable=False)

    event: Mapped[Event] = relationship(back_populates="expenses")
