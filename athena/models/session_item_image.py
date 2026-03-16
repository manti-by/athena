from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from athena.models.base import Base
from athena.models.mixings import TimestampMixin


class SessionItemImage(Base, TimestampMixin):
    __tablename__ = "session_item_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("session_items.id"), nullable=False)
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("images.id"), nullable=False)

    session_item: Mapped["SessionItem"] = relationship(back_populates="images")  # noqa: F821
    image: Mapped["Image"] = relationship(back_populates="session_items")  # noqa: F821
