# Orbit Cloud security

`orbit-cloud` and its initial adapters expose read-only inventory operations. This reduces mutation
risk but does not make returned metadata public or harmless. Resource IDs, names, scopes, labels, and
provider cursors can reveal account structure or operational details. Treat them according to your
data classification and do not put credentials in scopes or query filters.

The common model bounds query dimensions, cursor sizes, resource counts, and metadata lengths. Its
repr hides scopes, resource IDs, names, labels, and cursors. It excludes arbitrary raw provider
payloads. These controls limit accidental exposure and resource use; they are not a substitute for
access control, output filtering, or safe application logging.

Use workload identity or the provider SDK's supported credential chain where possible. Otherwise,
load secrets from a secret manager. Apply least privilege for the inventory API and selected scope,
verify TLS certificates, and restrict network egress to the provider endpoints required by the
adapter. Do not enable provider index/setup permissions merely to make inventory work unless your
cloud administrators have separately approved that configuration.

Provider errors are translated into sanitized common errors. Avoid logging exception context or raw
SDK errors. Page cursors are opaque and must not be logged. See each adapter's security guide for
provider-specific permissions and limitations.

This documentation is not an independent security audit. Provider service policy, IAM configuration,
identity lifecycle, and production deployment remain the operator's responsibility.
