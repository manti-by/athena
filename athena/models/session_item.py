import logging
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from athena.models.base import Base
from athena.models.mixins import TimestampMixin
from athena.services.image import read_image_mimetype_and_data
from athena.settings import get_settings


if TYPE_CHECKING:
    from athena.models.session import Session
    from athena.models.session_item_image import SessionItemImage


logger = logging.getLogger(__name__)
settings = get_settings()


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
            image_path = Path(settings.UPLOAD_DIR) / image.image.file_path
            if image_data := await read_image_mimetype_and_data(image_path=str(image_path)):
                mime_type, encoded_string = image_data
                result.append(f"data:{mime_type};base64,{encoded_string}")
        return result
