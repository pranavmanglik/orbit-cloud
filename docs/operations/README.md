# Orbit Cloud operations

`orbit-cloud` is a contract-only package and owns no network resources. Each provider adapter owns
one or more asynchronous SDK clients and must close them during application shutdown with
`aclose()`. Client creation is lazy; request timeouts, page sizes, and in-flight provider calls are
bounded by adapter configuration.

Inventory calls are read-only, but resource names, labels, scopes, and page cursors can still be
sensitive. Do not log full provider responses, credentials, or page cursors. Keep explicit identity
material in a secret manager and prefer workload identity or the provider SDK's standard credential
chain. Grant only the read permissions required by the selected inventory API.

Cloud inventory can be delayed, permission-filtered, partially indexed, or truncated by provider
limits. Check the returned `partial` flag and provider-specific documentation. Do not use an
inventory result as proof that a resource does not exist or that a policy is compliant.

## Local development

Adapter unit tests use fake asynchronous SDK clients and require no cloud credentials. Live checks
must be explicitly enabled and run only against a dedicated non-production account, project, or
subscription. A successful fake-client suite is not evidence of cloud API, identity, quota, or
network compatibility.
