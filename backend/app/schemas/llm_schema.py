from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


ResultType = Literal[
    "INVALID_PAGE",
    "EMPTY_CONTENT",
    "ONLY_FILES",
    "ONLY_TEXT",
    "TEXT_AND_FILES",
    "FAILED",
]


class ContentSection(BaseModel):
    heading: str = ""
    content: str = ""


class AttachmentResult(BaseModel):
    name: str = ""
    type: str = ""
    url: str = ""
    description: str = ""


class LLMResult(BaseModel):
    result_type: ResultType
    is_valid: bool
    title: str = ""
    summary: str = ""
    main_content: str = ""
    content_sections: List[ContentSection] = Field(default_factory=list)
    attachments: List[AttachmentResult] = Field(default_factory=list)
    invalid_reason: Optional[str] = None
    confidence: float = 0.0
