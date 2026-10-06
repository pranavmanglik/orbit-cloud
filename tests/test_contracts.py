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
"""Contract validation and protocol checks for bounded cloud inventory."""

from typing import Any

import pytest

from orbit_cloud import (
    CloudConfigurationError,
    CloudInventoryPage,
    CloudInventoryProvider,
    CloudInventoryQuery,
    CloudOperationError,
    CloudResource,
)


def test_inventory_models_accept_normalized_metadata() -> None:
    query = CloudInventoryQuery(
        scope="projects/demo",
        resource_types=("compute.googleapis.com/Instance",),
        locations=("us-central1",),
    )
    resource = CloudResource(
        provider="gcp",
        resource_id="//compute.googleapis.com/projects/demo/zones/us-central1-a/instances/web",
        resource_type="compute.googleapis.com/Instance",
        name="web",
        location="us-central1-a",
        labels={"environment": "test"},
    )
    page = CloudInventoryPage(resources=(resource,), next_page_token="opaque-token")

    assert query.page_size == 100
    assert page.resources[0].provider == "gcp"
    assert page.next_page_token == "opaque-token"
    assert "projects/demo" not in repr(query)
    assert "//compute.googleapis.com" not in repr(page)
    assert "opaque-token" not in repr(page)


@pytest.mark.parametrize(
    "values",
    [
        {"scope": ""},
        {"scope": " projects/demo"},
        {"scope": "projects/demo\n"},
        {"scope": "projects/demo", "page_size": 0},
        {"scope": "projects/demo", "page_size": 501},
        {"scope": "projects/demo", "page_size": True},
        {"scope": "projects/demo", "resource_types": ("type", "type")},
        {"scope": "projects/demo", "locations": ("bad region",)},
        {"scope": "projects/demo", "page_token": "bad\ntoken"},
    ],
)
def test_query_rejects_invalid_or_unbounded_input(values: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        CloudInventoryQuery(**values)


def test_resource_rejects_raw_payload_and_invalid_metadata() -> None:
    with pytest.raises(ValueError):
        CloudResource(provider="AWS", resource_id="arn:x", resource_type="x:y")
    with pytest.raises(ValueError):
        CloudResource(provider="aws", resource_id="arn:x?token=secret", resource_type="x:y")
    with pytest.raises(ValueError):
        CloudResource(
            provider="aws",
            resource_id="arn:aws:ec2:region:123:instance/i-1",
            resource_type="ec2:instance",
            raw_response={"secret": "must-not-be-representable"},
        )


def test_page_rejects_too_many_resources() -> None:
    resource = CloudResource(provider="aws", resource_id="arn:aws:x", resource_type="x:y")
    with pytest.raises(ValueError):
        CloudInventoryPage(resources=(resource,) * 501)


def test_provider_protocol_is_runtime_checkable() -> None:
    class Adapter:
        async def list_resources(self, query: CloudInventoryQuery) -> CloudInventoryPage:
            return CloudInventoryPage(resources=())

        async def aclose(self) -> None:
            return None

    assert isinstance(Adapter(), CloudInventoryProvider)


def test_errors_are_safe_and_retry_guidance_is_explicit() -> None:
    error = CloudOperationError("throttled", "The provider limited the request.", retryable=True)
    assert error.code == "throttled"
    assert error.retryable is True
    assert str(error) == "The provider limited the request."
    with pytest.raises(ValueError):
        CloudOperationError("ProviderError", "unsafe code")
    with pytest.raises(ValueError):
        CloudOperationError("failed", "secret\nvalue")

    config_error = CloudConfigurationError("invalid scope")
    assert str(config_error) == "invalid scope"
