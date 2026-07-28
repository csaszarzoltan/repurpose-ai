"""Format Template Registry.

Defines the FormatTemplate model and FormatRegistry for managing
content format prompt templates.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.models.content import ContentFormat


class FormatTemplate(BaseModel):
    """A prompt template for a specific content format."""

    format_id: ContentFormat
    name: str
    description: str
    max_length: int
    supports_images: bool
    supports_links: bool
    tone_guidance: str
    structure_hints: str
    target_audience: str
    system_prompt: str
    user_prompt_template: str


class FormatRegistry:
    """Registry managing FormatTemplate instances.

    Thread-safe by design: populated at startup and read-only during operation.
    """

    def __init__(self) -> None:
        self._templates: dict[ContentFormat, FormatTemplate] = {}

    def register(self, template: FormatTemplate) -> None:
        """Register a format template.

        Raises ValueError if a template for the same format_id already exists.
        """
        if template.format_id in self._templates:
            raise ValueError(
                f"Template for '{template.format_id}' already registered"
            )
        self._templates[template.format_id] = template

    def get(self, format_id: ContentFormat) -> FormatTemplate:
        """Get a template by format_id.

        Raises KeyError if the format_id has not been registered.
        """
        if format_id not in self._templates:
            raise KeyError(f"No template registered for '{format_id}'")
        return self._templates[format_id]

    def list_all(self) -> list[FormatTemplate]:
        """Return a copy of all registered templates (defensive copy)."""
        return list(self._templates.values())
