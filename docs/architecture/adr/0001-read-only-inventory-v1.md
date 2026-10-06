# ADR 0001: Read-only resource inventory for cloud v1

**Status:** Accepted for pre-alpha implementation  
**Date:** 2026-10-06

## Context

The previous draft exposed generic provision, inspect, and delete operations over arbitrary
resource configuration. AWS, Google Cloud, and Azure do not share portable resource schemas,
idempotency guarantees, consistency semantics, or deletion behavior. Generic mutation would make the
interface look more uniform than the providers are and create high-impact failure modes before a
concrete resource domain is selected.

The Orbit ecosystem needs a useful first cloud layer that can be implemented against real APIs,
used by operations tooling, and tested without granting write permissions.

## Decision

- V1 of `orbit-cloud` is a bounded, asynchronous, read-only resource inventory contract.
- `CloudInventoryQuery` standardizes scope, exact provider-native resource type and location
  filters, page size, and opaque page cursor.
- `CloudInventoryPage` returns normalized resource identifiers, types, display names, locations,
  and bounded labels. Raw provider response payloads are excluded.
- `orbit-cloud-aws`, `orbit-cloud-gcp`, and `orbit-cloud-azure` implement the contract with
  AWS Resource Explorer, Google Cloud Asset Inventory, and Azure Resource Graph respectively.
- Provider SDKs, credentials, query translation, pagination behavior, failures, and resource
  lifecycle remain in their adapter repositories.
- The previous generic mutation API is removed before a stable release. Add write operations only
  as a separate capability or concrete resource contract after defining provider-specific behavior,
  idempotency, permissions, and rollback expectations.
- The Python capability package is the Python SDK. Separate Go or Rust variants require a concrete
  workload and conformance/performance evidence; network-bound inventory alone is not sufficient.

## Alternatives considered

- Keep generic provision/delete methods: rejected because resource schemas and mutation semantics
  are not portable and the interface would suggest unverified safety guarantees.
- Start with compute-instance lifecycle: deferred because it requires a new shared resource spec,
  provider permissions, rollback rules, and live non-production validation for each cloud.
- Start with inventory: selected because all three providers have read-oriented inventory APIs and
  least-privilege operation is possible.

## Consequences

The contract is read-only and useful for inventory and operational tooling without mutating customer
infrastructure. Its result coverage is provider- and permission-dependent, and does not prove that
resources are absent or policy-compliant. Cursors remain provider-specific. Provider APIs are not
claimed to be strongly consistent.

## Validation still required

Local fake-client tests verify translation, bounds, cancellation, lifecycle, and safe errors. Live
provider calls, IAM policy review, provider pagination and partial-result behavior, hosted CI,
release provenance, and production topology validation remain external release gates.
