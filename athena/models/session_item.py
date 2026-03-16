from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from athena.models.base import Base
from athena.models.mixings import TimestampMixin


class SessionItem(Base, TimestampMixin):
    __tablename__ = "session_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    session: Mapped["Session"] = relationship(back_populates="items")  # noqa: F821
    images: Mapped[list["SessionItemImage"]] = relationship(  # noqa: F821
        back_populates="session_item", cascade="all, delete-orphan"
    )
