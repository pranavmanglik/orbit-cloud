# Orbit Cloud roadmap

This package and its adapters are pre-alpha. The current implemented scope is a provider-neutral,
read-only inventory contract with AWS Resource Explorer, Google Cloud Asset Inventory, and Azure
Resource Graph adapters. Local fake-client tests do not imply live-provider support or release
readiness.

## Priorities

1. Validate pagination, partial-result signaling, permission failures, identity setup, and API limits
   against dedicated non-production cloud environments.
2. Run the package CI on all declared Python versions and review the provider SDK dependency ranges.
3. Gather operator feedback on whether inventory is useful to `orbit-admin` or a future deployment
   package before adding consumers or expanding the contract.
4. Add additional provider-neutral filters only when all supported adapters can define their exact
   meaning and compatibility behavior.
5. Consider write-capable resource operations only as a separately designed contract for a concrete
   resource type, with explicit idempotency, authorization, rollback, and live failure testing.
6. Consider language-specific runtimes only where a concrete workload and conformance or benchmark
   evidence justifies their additional maintenance.
7. Close security, artifact integrity, provenance, hosted CI, and live-provider validation before a
   stable release.

There are no dated delivery promises. Provider availability does not imply production certification.
