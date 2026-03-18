from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from athena.models.base import Base
from athena.models.mixins import TimestampMixin
from athena.models.session_item import SessionItem


class Session(Base, TimestampMixin):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    items: Mapped[list["SessionItem"]] = relationship(  # noqa: F821
        back_populates="session", cascade="all, delete-orphan"
    )
