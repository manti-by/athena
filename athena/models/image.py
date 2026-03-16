from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from athena.models.base import Base
from athena.models.mixings import TimestampMixin


class Image(Base, TimestampMixin):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)

    session_items: Mapped[list["SessionItemImage"]] = relationship(  # noqa: F821
        back_populates="image"
    )
