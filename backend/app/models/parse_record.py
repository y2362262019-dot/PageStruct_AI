from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class ParseRecord(TimestampMixin, Base):
    __tablename__ = "parse_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("task.id"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    final_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    http_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fetch_status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execute_status: Mapped[str] = mapped_column(Text, nullable=False, default="PENDING")
    result_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    clean_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    main_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fetch_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    llm_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    txt_file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    docx_file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    task: Mapped["Task"] = relationship(back_populates="records")
    attachments: Mapped[List["Attachment"]] = relationship(
        back_populates="record",
        cascade="all, delete-orphan",
    )
