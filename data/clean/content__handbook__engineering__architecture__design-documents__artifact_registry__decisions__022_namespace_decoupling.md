## Status

**Proposed.**

## Context

[ADR-001](001_organizations_as_anchor_point.md) makes Organizations the anchor point for the Artifact Registry.
Referencing the Rails organization directly, by its ID in tables and tokens and by its path in URLs, has two costs.

Organization paths are mutable: companies rename. With the path in Artifact Registry URLs, every rename breaks client
configurations (`.npmrc`, `settings.xml`, Dockerfiles, CI pipelines), invalidates cached references, makes token
scopes stale, and needs rename propagation and race handling between Rails and the Artifact Registry. Repository names
are immutable for the same reasons ([ADR-009](009_api_design.md#repository-name-immutability)), and the same principle
applies one level up.

The organizational hierarchy is also still developing: nested organizations and organization merges are possible, and
organization rollout is not universal. Tight coupling to the organization ID would be costly to undo if the anchor
entity changes. So the Artifact Registry references its anchor through an indirection it owns.

Organizations remain the default anchor. The question is how the Artifact Registry references them: directly, or
through an internal namespace with its own immutable identifier.

## Proposal

Introduce an internal namespace entity in the Artifact Registry with three properties:

1. **Immutable slug**: a globally unique, customer-chosen, human-readable identifier that appears in all URLs and never
   changes, like a storage bucket name.
1. **Virtual anchor tuple**: a `(platform, entity_type, entity_id)` tuple that links the namespace to an external
   entity without interpreting its semantics.
1. **UUIDv7 ID**: used for database partitioning, internal queries, and as the namespace's stable resource identifier
   for authorization, the resource that role assignments target ([ADR-021](021_authorization.md#role-assignment)). It
   is not an addressing identifier: the slug is the only namespace identifier in client-facing URLs, while the internal
   GitLab API is keyed by the UUID ([ADR-009](009_api_design.md)).

This does not change [ADR-001](001_organizations_as_anchor_point.md); it adds an indirection between the Artifact
Registry and the anchor entity. No Rails identifier appears in the Artifact Registry's partitioning or URLs.

### Anchors

- `entity_id` is numeric for some anchor types and a UUID for others. The Artifact Registry never interprets the
  external entity's semantics; `entity_type` tells a consumer which entity the value identifies.
- The anchor is unique among namespaces that are not purged. Purging frees it, so its owner can onboard a new
  namespace, while the old slug stays retired
  ([ADR-015 (internal)](https://internal.gitlab.com/handbook/engineering/architecture/design-documents/artifact_registry/decisions/015_slug_policy/#slug-lifecycle)).
- For Organizations v1, every anchor is `('gitlab', 'organization', '<organizations.uuid>')`: the organization's
  UUIDv7, not its numeric ID. IAM's Relationships API rejects a non-UUIDv7 object id for the whole request it appears
  in, so the numeric ID could not name the organization ancestor.
- No other uniqueness may be placed on the organization value: [Organization Merges](#organization-merges) requires a
  surviving organization to hold more than one namespace.
- A new anchor type is a new `entity_type` value, with no schema change.
- A separate **billing anchor**, a `(billing_entity_type, billing_entity_id)` pair, identifies who pays for usage.
  The Artifact Registry stamps the stored pair on every billing event without interpreting its value, and checks only its type, when the pair is written.
  For Organizations v1 it is the top-level group, `('top_level_group', '<root_namespace_id>')`. Rails can replace it later when the payer changes (see
  [billing re-anchoring](#namespace-lifecycle)).
  The Artifact Registry accepts only the payer types it lists, so a new payer type, for example the organization when billing moves there, is an Artifact Registry change.
- The platform supplies every anchor and billing value at namespace creation.
  None has a schema default, so the Artifact Registry stays agnostic to the external identity and billing models beyond the payer types it accepts.

Partitioned tables key on `namespace_id`, or on the digest for blob storage
([ADR-007](007_database_schema.md#blob-storage-partitioning-strategy)), and neither changes. The Cells
[sharding key requirement](https://docs.gitlab.com/development/organization/sharding/#choosing-the-right-sharding-key)
applies to the Rails monolith's databases, not to a cell-local service: data movement across cells needs only that
rows are attributable to an organization, directly or indirectly. The namespace model provides
`namespace_id` → anchor → organization.

### Slug Design

The slug is chosen by the customer when creating a namespace and is exposed in every client surface. Its user-facing
name in customer documentation and UX is **registry handle**.

- **Immutable**: once set, it never changes.
- **Customer-chosen**: human-readable and typeable, since it appears in client configurations, CI pipelines, and
  Kubernetes manifests.
- **Globally unique**: no two namespaces can share a slug.
- **First in the path**: the slug is the first path segment after the API or protocol prefix in every client-facing
  URL except the OCI `GET /v2/` probe, and no numeric ID appears in any client-facing URL ([ADR-009](009_api_design.md)). With immutable repository names, the whole URL path
  is permanently stable.

Validation rules, default derivation from the organization name, reservation policy, and lifecycle controls (security
block and transfer) are defined in [ADR-015: Slug Policy (internal)](https://internal.gitlab.com/handbook/engineering/architecture/design-documents/artifact_registry/decisions/015_slug_policy/).

A request resolves its slug to the namespace ID with one indexed lookup. The mapping is immutable, so it can be cached
freely.

### Namespace Lifecycle

**Creation:** the customer chooses a slug, the namespace is linked to their organization through the anchor, and the
slug is claimed with the topology service for Cells routing.

**Organization rename:** no impact. Nothing changes in the database, URLs, tokens, or client configurations.

**Anchor change:** re-anchoring a namespace to a different entity updates only the anchor. The slug, the URLs and the
partitioned data do not change. For Organizations v1, no such events exist.

**Billing re-anchoring:** Rails can replace the billing anchor when the payer changes, for example when a paid group becomes the nominated group.
Re-anchoring changes neither the slug nor the anchor tuple.

**Status:** A namespace has two one-way lifecycle events, deletion and purge, and four independent, reversible service conditions:

- Blocked (security).
- Disabled (the organization turned the registry off).
- Suspended (the plan lapsed, see [ADR-010](010_data_retention.md#subscription-expiration)).
- Usage-limit blocked (the namespace reached its usage limit, see [ADR-010](010_data_retention.md#usage-limit-block)).

Applying or lifting one condition never changes another, so several conditions can apply at the same time.
A suspended or usage-limit-blocked namespace serves reads (pulls) and refuses writes (pushes).
Any other event or condition stops all service.
[ADR-010](010_data_retention.md#billing-and-retention-by-condition) sets how billing and retention apply under each condition.
The Artifact Registry stores each condition and enforces the status on every request, whatever Rails has cached, and exposes it through its API (see [Slug Discovery](#slug-discovery)).
It never learns why Rails set a condition.

**Deletion:** The Artifact Registry soft-deletes the namespace. The slug is reserved and cannot be reclaimed
by another customer, to avoid the same security risks as repository name reclaiming (authorization bypass, cache
poisoning). See [ADR-015 (internal)](https://internal.gitlab.com/handbook/engineering/architecture/design-documents/artifact_registry/decisions/015_slug_policy/#slug-lifecycle) for the full lifecycle (soft-delete window allowing
reclaim, hard-delete with permanent retirement) and the security-block and transfer controls.

### Organization Merges

If organizations merge, the namespace model needs no data migration:

1. The anchor on the absorbed organization's namespace is updated to point to the surviving organization: one metadata
   update per namespace.
1. The surviving organization holds several namespaces, each with its own repositories and its own deduplication
   boundary.
1. Nothing moves across database partitions or in object storage, because all stored data is keyed by namespace, not
   organization.
1. Slugs do not change, so URLs, tokens and client configurations stay stable.

Consolidating into a single namespace would be an explicit migration of repositories between namespaces, not an
automatic consequence of the merge.

Without the namespace, a merge would mean migrating all partitioned data from one organization ID to another,
changing every URL, reconciling deduplication boundaries, and handling stale token scopes.

### Cells Routing

The topology service maps claimed identifiers to cells, and the Artifact Registry claims slugs:

1. When a namespace is created, the Artifact Registry claims its slug, mapping it to the cell that holds its data.
1. The HTTP router extracts the slug from the URL and routes the request to that cell. The slug is readable without
   authentication, so it routes every slug-prefixed request. ADR-009 decides how the routes without a slug reach a
   cell: the OCI [`GET /v2/` probe](009_api_design.md#container) and the UUID-keyed
   [GitLab API](009_api_design.md#gitlab-api).

Only namespace creation needs the topology service to be writable. The read path needs only the routing lookup, which
can be cached.

### Slug Discovery

The GitLab frontend reaches the Artifact Registry through the Rails monolith ([ADR-014](014_frontend_to_artifact_registry.md)). Every Artifact Registry API call requires the slug in the URL, so Rails needs the slug before it can make any request.

Rails durably stores only the namespace UUID, one row per namespace, written at provisioning. For Organizations v1, that is a single row per organization; an [organization merge](#organization-merges) would add the absorbed namespace's row to the surviving organization. The UUID is immutable, so this reference never needs synchronization and survives merges and anchor changes.

The slug and the namespace status are not persisted on the Rails side. Rails resolves them from the Artifact Registry by UUID and caches them.
The slug can change only on the Artifact Registry's authority, through a legal escalation, the one exception to its immutability.
The service conditions ([Namespace Lifecycle](#namespace-lifecycle)) have two sources: Rails sets disabled, suspended and usage-limit blocked, and the Artifact Registry sets blocked (security).
The Artifact Registry is authoritative for enforcing every condition on each request.
In the hybrid deployment model (Self-Managed Rails against a SaaS Artifact Registry), slug changes and security blocks can only originate on the Artifact Registry side, so Rails cannot be their source of truth.

A stale cache never weakens enforcement: the Artifact Registry enforces the namespace status on every request. For the status, staleness only affects display (for example, the navigation briefly showing the registry while the namespace is disabled) until the next refresh. For the slug, a stale value can render broken links until the next refresh; slug changes are rare emergency events, and the cache refresh interval bounds that window.

## Consequences

### Positive

1. **Rails decoupling**: no Rails IDs in the Artifact Registry's partitioning or URLs. If Rails changes
   organization IDs or structure, the Artifact Registry is unaffected.
1. **Immutable URLs**: both the slug and repository names are immutable, so no rename breaks a URL, a token scope or a
   client configuration.
1. **Stable partitioning**: namespace IDs are internal and never change, even when the anchor changes.
1. **Anchor flexibility**: namespaces attach to organizations today and to other entities later, with no schema change
   or data movement.
1. **Cells-ready**: slug claiming gives a routing key that does not depend on organization path resolution.
1. **No Rails call on the request path**: the Artifact Registry resolves the namespace from its own data.
1. **Organization merges without data migration** ([Organization Merges](#organization-merges)).
1. **Standalone product potential**: because the Artifact Registry owns its namespace identity and treats the anchor as
   opaque, it does not structurally depend on GitLab Rails. It could be packaged as an independent product that relies
   on a third-party authentication and authorization provider.

### Negative

1. **Slug squatting**: globally unique slugs invite squatting, which needs a policy for reserved names, high-value
   slugs and minimum length ([ADR-015 (internal)](https://internal.gitlab.com/handbook/engineering/architecture/design-documents/artifact_registry/decisions/015_slug_policy/)).
1. **Namespace creation is an explicit action**: a namespace must be provisioned before any client request can
   succeed. The Artifact Registry cannot serve an organization that has not set one up.
1. **Topology service dependency**: the Artifact Registry integrates the topology service to claim slugs.
1. **Slug discoverability**: unlike organization paths, which users already know from GitLab, the slug is a new
   concept. Client configuration documentation and the UI need to surface it.
1. **Deduplication boundary**: deduplication moves from the organization
   ([ADR-002](002_storage_deduplication_scope.md)) to the namespace. For
   Organizations v1 a namespace maps one-to-one to an organization, but an organization with several namespaces has an
   independent deduplication boundary in each. Cross-namespace deduplication is out of scope.

## References

- [ADR-001: Organizations as Anchor Point](001_organizations_as_anchor_point.md)
- [ADR-002: Storage Deduplication Scope](002_storage_deduplication_scope.md)
- [ADR-009: API Design](009_api_design.md)
- [ADR-014: Frontend to Artifact Registry Interaction](014_frontend_to_artifact_registry.md)
- [ADR-015: Slug Policy (internal)](https://internal.gitlab.com/handbook/engineering/architecture/design-documents/artifact_registry/decisions/015_slug_policy/)
- [ADR-021: Authorization](021_authorization.md)
