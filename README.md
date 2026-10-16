# Orbit Cloud

`orbit-cloud` defines the provider-neutral asynchronous contract for **read-only cloud resource
inventory**. Provider adapters implement the contract and own vendor SDKs, credentials, query
translation, provider errors, and client lifecycle.

```text
orbit-cloud
├── orbit-cloud-aws
├── orbit-cloud-gcp
└── orbit-cloud-azure
```

**Status:** unpublished v0.1.0-alpha review candidate. The contract and three adapter implementations are under active development.
This does not imply live cloud validation, production certification, or release readiness.

## Install

Install the capability and the provider you use:

```bash
python -m pip install orbit-cloud orbit-cloud-aws
```

## Use the common contract

```python
from orbit_cloud import CloudInventoryQuery
from orbit_cloud_aws import AWSCloudInventory, AWSCloudInventoryConfig

provider = AWSCloudInventory(
    AWSCloudInventoryConfig(
        region_name="us-east-1",
        view_arn="arn:aws:resource-explorer-2:us-east-1:123456789012:view/Inventory/unique-id",
    )
)
try:
    page = await provider.list_resources(
        CloudInventoryQuery(
            scope="arn:aws:resource-explorer-2:us-east-1:123456789012:view/Inventory/unique-id",
            resource_types=("ec2:instance",),
            locations=("us-east-1",),
            page_size=100,
        )
    )
    for resource in page.resources:
        print(resource.resource_type, resource.resource_id)
finally:
    await provider.aclose()
```

`scope` is an opaque provider-native identifier: a Resource Explorer view ARN for AWS, a project,
folder, or organization path for Google Cloud, or a subscription identifier for Azure. Continue
pagination with the returned `next_page_token` and the exact same scope and filters. Tokens are
opaque, provider-specific, bounded, and should not be logged.

The common result contains only normalized resource ID, type, display name, location, and optionally
bounded labels. The initial adapters omit labels and raw provider payloads to limit disclosure.
Resource pages and label mappings are detached immutable values; serialization produces ordinary
JSON-compatible dictionaries.
Inventory results can be eventually consistent, filtered by permissions, or incomplete; consult
each adapter's documentation and its `partial` result flag.

The common query supports exact provider resource types and locations. Their identifiers retain
provider spelling. Provider-specific query languages are not accepted as common input.

## Safety and lifecycle

All v1 operations are read-only. No adapter provisions, changes, or deletes cloud resources. The
packages use the provider's normal workload identity or SDK credential chain; there are no default
credentials. Give each identity only inventory permissions, store any explicit credentials in a
secret manager, and use TLS verification.

Adapters use bounded page sizes and concurrency, finite network timeouts, cancellation-aware async
SDKs, sanitized provider errors, lazy client creation, and idempotent `aclose()` methods. Close each
provider during application shutdown. Package tests use fake SDK clients and do not require cloud
credentials; live behavior still needs validation in a dedicated non-production environment.

## Provider adapters

- [`orbit-cloud-aws`](https://github.com/orbit-projects/orbit-cloud-aws) queries AWS Resource
  Explorer through an async AWS SDK client. A Resource Explorer view and read permissions are
  required; indexed inventory may be partial or eventually consistent.
- [`orbit-cloud-gcp`](https://github.com/orbit-projects/orbit-cloud-gcp) queries Cloud Asset
  Inventory using its async Python client. The API must be enabled and the identity needs
  `cloudasset.assets.searchAllResources` on the requested scope.
- [`orbit-cloud-azure`](https://github.com/orbit-projects/orbit-cloud-azure) queries Azure Resource
  Graph using the async Azure SDK and an async Azure identity credential.

The separate `orbit-storage` capability and its S3, GCS, and Azure Blob adapters continue to own
object storage. They do not depend on `orbit-cloud`.

## SDK and language policy

This Python package is the user-facing SDK for the Python framework. The initial adapters use the
provider's asynchronous Python SDK path. Cloud inventory is network-I/O-bound, so a separate Go or
Rust runtime is not included without a concrete workload and measured benefit. This follows the
[Core SDK and language-variant policy](https://github.com/orbit-projects/orbit-core/blob/main/docs/architecture/adr/0021-capability-sdk-and-language-variant-policy.md).

## Documentation and development

Read the [architecture](docs/architecture/overview.md), [operations](docs/operations/README.md),
[security](docs/security/overview.md), and [development](docs/development/README.md) guides.

```bash
python -m pip install -e '.[dev]' build
pytest
ruff check src tests
ruff format --check src tests
mypy
python -m build
```

Licensed under Apache-2.0.
