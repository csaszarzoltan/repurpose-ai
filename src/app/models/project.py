"""Persistent content-project models used by the user workspace."""
from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

from app.models.content import BrandVoice, ContentFormat


class ProjectStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    ARCHIVED = "archived"


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=100_000)
    source_format: ContentFormat = ContentFormat.BLOG_POST
    target_formats: list[ContentFormat] = Field(min_length=1, max_length=10)
    brand_voice: BrandVoice = BrandVoice.PROFESSIONAL
    custom_instructions: str | None = Field(default=None, max_length=2_000)

    @field_validator("title", "body")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("target_formats")
    @classmethod
    def unique_formats(cls, values: list[ContentFormat]) -> list[ContentFormat]:
        return list(dict.fromkeys(values))


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = Field(default=None, min_length=1, max_length=100_000)
    target_formats: list[ContentFormat] | None = Field(default=None, min_length=1, max_length=10)
    brand_voice: BrandVoice | None = None
    custom_instructions: str | None = Field(default=None, max_length=2_000)
    status: ProjectStatus | None = None

    @field_validator("title", "body")
    @classmethod
    def not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("must not be blank")
        return value.strip() if value is not None else value


class ProjectResponse(BaseModel):
    id: str
    owner_id: str
    title: str
    body: str
    source_format: ContentFormat
    target_formats: list[ContentFormat]
    brand_voice: BrandVoice
    custom_instructions: str | None = None
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime


class WorkspaceSummary(BaseModel):
    """Small attention summary for the repeated daily workspace workflow."""

    active_projects: int = 0
    projects_without_drafts: int = 0
    draft_variants: int = 0
    approved_variants: int = 0
    fallback_variants_needing_review: int = 0


class TelemetryEvent(BaseModel):
    event_name: str = Field(pattern=r"^(workspace_viewed|project_created|project_updated|project_archived|generation_started)$")
    properties: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("properties")
    @classmethod
    def reject_sensitive_properties(cls, value: dict) -> dict:
        blocked = {"content", "body", "title", "prompt", "token", "secret", "password", "api_key"}
        found = blocked.intersection(key.lower() for key in value)
        if found:
            raise ValueError(f"sensitive telemetry properties are not allowed: {', '.join(sorted(found))}")
        if len(value) > 20:
            raise ValueError("at most 20 telemetry properties are allowed")
        return value

class VariantStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"


class VariantUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=100_000)
    status: VariantStatus = VariantStatus.DRAFT

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class VariantResponse(BaseModel):
    id: str
    project_id: str
    owner_id: str
    format: ContentFormat
    content: str
    version: int
    status: VariantStatus
    generation_mode: str
    created_at: datetime


class GenerationResponse(BaseModel):
    project_id: str
    generation_mode: str
    warning: str | None = None
    variants: list[VariantResponse]


class RecipeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    target_formats: list[ContentFormat] = Field(min_length=1, max_length=10)
    brand_voice: BrandVoice = BrandVoice.PROFESSIONAL
    custom_instructions: str | None = Field(default=None, max_length=2_000)

    @field_validator("name")
    @classmethod
    def recipe_name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("target_formats")
    @classmethod
    def recipe_formats_unique(cls, values: list[ContentFormat]) -> list[ContentFormat]:
        if len(values) != len(set(values)):
            raise ValueError("target formats must be unique")
        return values


class RecipeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    target_formats: list[ContentFormat] | None = Field(default=None, min_length=1, max_length=10)
    brand_voice: BrandVoice | None = None
    custom_instructions: str | None = Field(default=None, max_length=2_000)

    @field_validator("name")
    @classmethod
    def updated_recipe_name_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("target_formats")
    @classmethod
    def updated_recipe_formats_unique(
        cls, values: list[ContentFormat] | None
    ) -> list[ContentFormat] | None:
        if values is not None and len(values) != len(set(values)):
            raise ValueError("target formats must be unique")
        return values


class RecipeResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    target_formats: list[ContentFormat]
    brand_voice: BrandVoice
    custom_instructions: str | None = None
    created_at: datetime
    updated_at: datetime


class RecipeProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=100_000)
    source_format: ContentFormat = ContentFormat.BLOG_POST

    @field_validator("title", "body")
    @classmethod
    def recipe_project_fields_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value
