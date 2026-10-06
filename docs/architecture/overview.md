# Orbit Cloud architecture

`orbit-cloud` owns the provider-neutral Python contract for bounded, asynchronous, **read-only**
resource inventory. It contains normalized models, input bounds, stable safe errors, and the
`CloudInventoryProvider` protocol. It does not import Core, cloud SDKs, or provider credentials.

Provider adapters implement the capability and own vendor SDKs, credential discovery, transport,
query translation, pagination mapping, provider-specific errors, and client lifecycle:

```text
Orbit application
├── orbit-core
├── orbit-cloud
└── one or more explicitly selected adapters
    ├── orbit-cloud-aws
    ├── orbit-cloud-gcp
    └── orbit-cloud-azure
```

## Common contract

`CloudInventoryQuery` contains a provider-native `scope`, exact provider-native resource type and
location filters, a bounded page size, and an optional opaque page token. Provider-native values
are accepted as identifiers; arbitrary provider query languages are not part of the portable
contract. Each adapter translates the same fields into its provider API.

`CloudInventoryPage` returns only bounded normalized resource metadata and an optional provider
cursor. A cursor must be replayed with the same scope, filters, and page size, and may expire or
become invalid according to provider behavior. An adapter marks partial results when its provider
reports incomplete coverage; it does not claim that inventory is globally complete or strongly
consistent.

The `CloudResource` model intentionally excludes arbitrary raw provider documents. It exposes
resource ID, type, name, location, and optional bounded labels. The initial adapters omit labels.
Adapters reject malformed provider pages with sanitized errors instead of silently dropping
records, and map SDK failures to
`CloudOperationError` values with explicit retry guidance. Caller cancellation propagates through
asynchronous SDK calls. Clients are created lazily,
bounded by adapter concurrency and request timeouts, and closed by `aclose()`.

## Provider choice

- AWS Resource Explorer provides indexed resource search, with view permissions, coverage, and
  consistency controlled by AWS configuration.
- Google Cloud Asset Inventory provides scoped resource search and server-side type/location filters.
- Azure Resource Graph provides scoped resource queries and provider continuation tokens.

These services differ in coverage, indexing delay, permissions, and pagination. The common model
does not erase those differences. Provider-specific guides document setup and limitations.

Object storage remains under `orbit-storage` and the S3, GCS, and Azure Blob adapters. Those service
integrations do not depend on `orbit-cloud`.

## Language and SDK decision

The capability package is the Python SDK for Orbit applications. The first adapters use async Python
clients because they spend their time waiting on remote inventory APIs. Go or Rust variants would
add independent compatibility and release surfaces without an established workload or benchmark
showing an advantage. Add one only after conformance tests and representative measurements support
it, following [ADR 0021](https://github.com/orbit-projects/orbit-core/blob/main/docs/architecture/adr/0021-capability-sdk-and-language-variant-policy.md).
