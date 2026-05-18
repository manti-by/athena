import enum
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from athena.models.base import Base
from athena.models.mixins import TimestampMixin


if TYPE_CHECKING:
    from athena.models.session_item_image import SessionItemImage


class ImageSource(enum.Enum):
    USER = "USER"
    OPENROUTER = "OPENROUTER"


class Image(Base, TimestampMixin):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    source: Mapped[ImageSource] = mapped_column(nullable=False, default=ImageSource.USER)

    session_items: Mapped[list["SessionItemImage"]] = relationship(  # noqa: F821
        back_populates="image"
    )
