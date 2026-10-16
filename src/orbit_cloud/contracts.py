# Copyright 2026-present Orbit Contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Bounded provider-neutral cloud resource inventory contracts."""

from __future__ import annotations

import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    StrictStr,
    ValidationInfo,
    field_serializer,
    field_validator,
)

_MAX_PAGE_SIZE = 500
_MAX_PAGE_TOKEN = 8192
_MAX_RESOURCE_TYPES = 100
_MAX_LOCATIONS = 100
_MAX_LABELS = 64
_MAX_LABEL_TEXT = 256
_IDENTIFIER = re.compile(r"(?:[A-Za-z0-9]|/)[A-Za-z0-9:._/+_-]{0,2047}\Z")
_PROVIDER = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")


def _bounded_text(value: str, *, field: str, maximum: int) -> str:
    """Require trimmed printable text without changing provider-native identifier spelling."""
    if not value or len(value) > maximum or value != value.strip():
        raise ValueError(f"{field} must be non-empty, trimmed text within its length limit.")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError(f"{field} cannot contain control characters.")
    return value


class CloudResource(BaseModel):
    """Safe, normalized resource metadata; raw provider payloads are deliberately excluded."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    provider: StrictStr = Field(min_length=1, max_length=64)
    resource_id: StrictStr = Field(min_length=1, max_length=2048, repr=False)
    resource_type: StrictStr = Field(min_length=1, max_length=512)
    name: StrictStr | None = Field(default=None, max_length=512, repr=False)
    location: StrictStr | None = Field(default=None, max_length=256)
    labels: Mapping[StrictStr, StrictStr] = Field(
        default_factory=dict, max_length=_MAX_LABELS, repr=False
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        """Require a lowercase provider identifier with a bounded package-style shape."""
        if _PROVIDER.fullmatch(value) is None:
            raise ValueError("Provider must be a lowercase package-style identifier.")
        return value

    @field_validator("resource_id", "resource_type", "name", "location")
    @classmethod
    def validate_metadata_text(cls, value: str | None, info: ValidationInfo) -> str | None:
        """Bound provider metadata and reject control characters before it is exposed."""
        if value is not None:
            field_name = info.field_name or "metadata"
            maximum = 2048 if field_name == "resource_id" else 512
            value = _bounded_text(value, field=field_name, maximum=maximum)
        return value

    @field_validator("resource_id", "resource_type")
    @classmethod
    def validate_identifiers(cls, value: str) -> str:
        """Reject unsupported characters in resource identifiers and types."""
        if _IDENTIFIER.fullmatch(value) is None:
            raise ValueError("Resource identifiers contain unsupported characters.")
        return value

    @field_validator("labels")
    @classmethod
    def validate_labels(cls, value: Mapping[str, str]) -> dict[str, str]:
        """Validate bounded, printable label keys and values."""
        copied = dict(value)
        for key, item in copied.items():
            _bounded_text(key, field="label key", maximum=_MAX_LABEL_TEXT)
            _bounded_text(item, field="label value", maximum=_MAX_LABEL_TEXT)
        return copied

    def model_post_init(self, __context: object) -> None:
        """Detach and freeze labels so a validated inventory page cannot change later."""
        object.__setattr__(self, "labels", MappingProxyType(dict(self.labels)))

    @field_serializer("labels")
    def serialize_labels(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize immutable provider labels as an ordinary dictionary."""
        return dict(value)


class CloudInventoryQuery(BaseModel):
    """A bounded common inventory query; ``scope`` and filter values use provider identifiers."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    scope: StrictStr = Field(min_length=1, max_length=1024, repr=False)
    resource_types: tuple[StrictStr, ...] = Field(default=(), max_length=_MAX_RESOURCE_TYPES)
    locations: tuple[StrictStr, ...] = Field(default=(), max_length=_MAX_LOCATIONS)
    page_size: StrictInt = Field(default=100, ge=1, le=_MAX_PAGE_SIZE)
    page_token: StrictStr | None = Field(default=None, max_length=_MAX_PAGE_TOKEN, repr=False)

    @field_validator("scope")
    @classmethod
    def validate_scope(cls, value: str) -> str:
        """Require a bounded printable provider scope."""
        return _bounded_text(value, field="scope", maximum=1024)

    @field_validator("resource_types", "locations")
    @classmethod
    def validate_filters(cls, values: tuple[str, ...], info: ValidationInfo) -> tuple[str, ...]:
        """Reject duplicate, oversized, or malformed resource filter identifiers."""
        field = info.field_name or "filters"
        if len(set(values)) != len(values):
            raise ValueError(f"{field} cannot contain duplicate values.")
        for value in values:
            _bounded_text(value, field=field, maximum=512)
            if _IDENTIFIER.fullmatch(value) is None:
                raise ValueError(f"{field} contain unsupported characters.")
        return values

    @field_validator("page_token")
    @classmethod
    def validate_page_token(cls, value: str | None) -> str | None:
        """Bound an opaque provider pagination cursor without interpreting it."""
        if value is not None:
            _bounded_text(value, field="page_token", maximum=_MAX_PAGE_TOKEN)
        return value


class CloudInventoryPage(BaseModel):
    """One bounded page of inventory results and an opaque provider cursor."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    resources: tuple[CloudResource, ...] = Field(max_length=_MAX_PAGE_SIZE)
    next_page_token: StrictStr | None = Field(default=None, max_length=_MAX_PAGE_TOKEN, repr=False)
    partial: StrictBool = False

    @field_validator("next_page_token")
    @classmethod
    def validate_page_token(cls, value: str | None) -> str | None:
        """Bound an opaque provider cursor returned for the next page."""
        if value is not None:
            _bounded_text(value, field="next_page_token", maximum=_MAX_PAGE_TOKEN)
        return value


class CloudError(Exception):
    """Base class for provider-neutral inventory errors."""


class CloudConfigurationError(CloudError, ValueError):
    """Raised when a query or provider configuration is invalid or unsupported."""


class CloudOperationError(CloudError):
    """Sanitized provider failure with a stable code and explicit retry guidance."""

    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        if not isinstance(code, str) or _PROVIDER.fullmatch(code) is None:
            raise ValueError("Cloud error codes must be lowercase identifiers.")
        if not isinstance(message, str) or not message or len(message) > 512:
            raise ValueError("Cloud error messages must contain 1 through 512 characters.")
        if any(ord(char) < 32 or ord(char) == 127 for char in message):
            raise ValueError("Cloud error messages cannot contain control characters.")
        if not isinstance(retryable, bool):
            raise TypeError("retryable must be a boolean.")
        self.code = code
        self.retryable = retryable
        super().__init__(message)


@runtime_checkable
class CloudInventoryProvider(Protocol):
    """Asynchronous, read-only inventory interface implemented by optional provider adapters."""

    async def list_resources(self, query: CloudInventoryQuery) -> CloudInventoryPage:
        """Return one page; repeat the same scope and filters when using its cursor."""

    async def aclose(self) -> None:
        """Close owned SDK clients and credentials; repeated close is safe."""


__all__ = [
    "CloudConfigurationError",
    "CloudError",
    "CloudInventoryPage",
    "CloudInventoryProvider",
    "CloudInventoryQuery",
    "CloudOperationError",
    "CloudResource",
]
