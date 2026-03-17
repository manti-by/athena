import base64
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from athena.models.base import Base
from athena.models.mixings import TimestampMixin


if TYPE_CHECKING:
    from athena.models.session import Session
    from athena.models.session_item_image import SessionItemImage


class SessionItem(Base, TimestampMixin):
    __tablename__ = "session_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    session: Mapped["Session"] = relationship(back_populates="items")  # noqa: F821
    images: Mapped[list["SessionItemImage"]] = relationship(  # noqa: F821
        back_populates="session_item", cascade="all, delete-orphan"
    )

    async def get_image_data_for_context(self) -> list[dict]:
        return [{"type": "image_url", "image_url": {"url": x}} for x in await self.get_image_data_list()]

    async def get_image_data_list(self) -> list[str]:
        result = []
        for image in self.images:
            with open(image.image.file_path, "rb") as image_file:
                image_bytes = image_file.read()
            encoded_bytes = base64.b64encode(image_bytes)
            encoded_string = encoded_bytes.decode("utf-8")
            result.append(f"data:image/jpeg;base64,{encoded_string}")
        return result
