## Context

The Artifact Registry API design has the following constraints:

1. **Three API categories**: Management APIs to interact with registry concepts, Artifact Management Client APIs that follow strict specifications to be used by specific clients, and a GitLab API for platform-to-registry communication.
1. **Follow the database data organization**: The API endpoints are organized by artifact format, matching the database schema, where each format family has its own tables and fields (`docker` and `oci` form one family). This mapping simplifies implementation by avoiding complex multi-format abstractions and enables format-specific optimizations.
1. **Three repository types**: The registry supports three repository types: hosted (private storage for pushed artifacts), remote (proxy/cache for external registries), and virtual (aggregated pull endpoint combining hosted and remote upstreams). This model matches industry practice. All three types are standalone, independently manageable entities.

The Artifact Registry is scoped to Organizations (see [ADR-001](001_organizations_as_anchor_point.md) for rationale) through an immutable, customer-chosen slug ([ADR-022](022_namespace_decoupling.md)) that appears in all customer-facing URLs. All client and management endpoints include the `/:slug` path segment after the API version prefix (or protocol prefix for client APIs), scoping every request to a specific slug. The slug provides stable [Cells](/handbook/engineering/architecture/design-documents/cells/) routing via the topology service without depending on organization path resolution. Two exceptions: the OCI-mandated `GET /v2/` version probe (see [Container](#container)) and the GitLab API endpoints (see [GitLab API](#gitlab-api)).

The Artifact Registry is served on a dedicated domain (for example, `artifact-registry.gitlab.com`), separate from the main GitLab application domain. This improves our security posture against [XSS](https://owasp.org/www-community/attacks/xss/) and [SSRF](https://owasp.org/www-community/attacks/Server_Side_Request_Forgery) vulnerabilities by isolating the registry from the main application's cookies, credentials, and internal network context.

This ADR defines the API surfaces and the rules that apply to them. The OpenAPI specifications and the per-format specifications in the Artifact Registry codebase define the routes and their payloads.

### Versioning

The Artifact Registry runs on a dedicated domain, so the `/api/v4` prefix used in the GitLab Rails monolith does not apply. The monolith uses `/api/v4` to separate API routes from web UI routes on the same domain and to reflect its API version lineage (v3 to v4).

Management API routes use an `/api/v1` path-based version prefix. The `/api/` prefix separates management routes from protocol-specific client routes on the same domain, preventing namespace collisions if the management API version is ever bumped (e.g., OCI mandates `/v2/`, so a bare `/v2` management prefix would collide). This is consistent with industry practice. Path-based versioning keeps the version visible in URLs, logs, and routing rules without requiring header inspection.

Client APIs do not use a version prefix. Protocol-specific versioning is handled by the clients themselves if necessary. This keeps client-configured URLs as short as possible.

GitLab API routes use an `/api/gitlab/v1` prefix. The explicit `gitlab` segment keeps the surface visible in URLs, logs, and routing rules, and lets the edge apply dedicated path rules to it. This follows the Container Registry precedent, whose registry-to-platform surface uses a `/gitlab/v1/` prefix.

### API Classification

The API surface is divided into three distinct categories which have different rules:

1. **Management APIs**: REST and GraphQL APIs for CRUD operations on registry concepts (repositories, artifacts, policies, etc.)
   - Authentication: the GitLab standard REST/GraphQL authentication
   - Purpose: UI, automation scripts, administrative tools
   - Format: JSON responses with standard GitLab API patterns. A route that returns a stored JSON document, such as a container manifest, returns it unchanged under the document's own media type
   - Pagination: All list endpoints are paginated, preferably using a keyset pagination strategy. A list that a limit keeps below one page, such as a virtual repository's upstreams, is not paginated

1. **Artifact Management Client APIs**: Protocol-specific APIs implementing industry-standard specifications
   - Authentication: Protocol-specific (Bearer tokens for OCI, Basic auth for Maven, etc.)
   - Purpose: Native client compatibility (`docker`, `npm`, `mvn`, `go` commands)
   - Format: Protocol-specific responses (OCI Distribution Spec, Maven Repository Layout, NPM Registry API, GOPROXY protocol)

1. **GitLab API**: REST endpoints for platform-to-registry communication
   - Authentication: Service-to-service credentials; no end-user identity
   - Purpose: Namespace provisioning, resolution, and service conditions; resource verifications
   - Format: JSON
   - Exposure: Trusted platform callers only

Management and Client APIs serve all three repository types: hosted, virtual, and remote. Client APIs are organized per protocol (one set of endpoints per protocol; the OCI Distribution Spec endpoints serve repositories of both the `docker` and `oci` formats), while Management APIs share a unified repository CRUD with format appearing only in format-specific sub-resources.

### URL Structure Design

Management API routes are **anchored at the repository**. The `/api/v1/:slug` prefix is mandatory for all routes and is not counted as a conceptual level. Repository endpoints accept a unique repository name as the `:repository_name` parameter.

All repository-level resources (artifacts, lifecycle policies, upstream associations) are scoped to a repository because hosted and remote repositories store data in separate, per-format-family tables.

The `:format` segment appears **after a repository** for all format-specific sub-resources: `/api/v1/:slug/repositories/:repository_name/:format/...` (e.g., listing images, lifecycle policies). Repository-level sub-resources are dedicated to a specific format, allowing higher flexibility in endpoints organization and customization of the returned structure. Namespace-level format-specific operations use `:format` as a prefix: `/api/v1/:slug/:format/statistics`.

Repository CRUD itself is format-free because every format and kind shares one repository resource. Format and kind are properties of the repository resource, not URL segments.

For example:

- Listing all repositories: `GET /api/v1/:slug/repositories`
- Creating a repository: `POST /api/v1/:slug/repositories`
- Reading/updating/deleting a repository: `GET/PATCH/DELETE /api/v1/:slug/repositories/:repository_name` (top-level route using the target concept identifier)
- Listing images in a container-family repository: `GET /api/v1/:slug/repositories/:repository_name/:format/images` (format-specific sub-resource; `:format` is `docker` or `oci`)
- Getting an image by ID: `GET /api/v1/:slug/repositories/:repository_name/:format/images/:image_id` (artifact detail, scoped to the repository)

### Repository Name Immutability

Repository names are set at creation time and cannot be changed. Repository descriptions remain mutable. This prevents broken client configurations, authorization bypass through name reclaim, and silent misrouting. It also enables name-based URLs (see [below](#human-friendly-urls)) and simplifies authorization rules. This is consistent with industry practice.

### Human-Friendly URLs

Repository names must be globally unique within the slug, regardless of format or repository type. This global uniqueness constraint matches industry practice and avoids ambiguous name-based lookups. It can be relaxed to per-format uniqueness later without breaking anyone; tightening would be a breaking change. Name immutability (see [above](#repository-name-immutability)) makes name-based URLs safe as stable path segments. Slugs are immutable ([ADR-022](022_namespace_decoupling.md)), so every segment in a URL path is human-readable and permanently stable.

## API Organization

### Management APIs

Management APIs use GitLab [REST API authentication](https://docs.gitlab.com/api/rest/authentication/).

**Note:** `:format` is the repository's `format` value. The `docker` and `oci` formats form the container family and share one artifact model: images, tags, and manifests. A request whose `:format` segment does not match the repository's format returns `404 Not Found`.

#### Namespace-level APIs

Namespace-level routes sit directly under `/api/v1/:slug`: the repository collection, namespace and per-format statistics, the namespace lifecycle policy, and the namespace itself. The repository list spans every format and kind, and filters by both.

The repository resource is polymorphic by format and kind. Fields every repository shares sit at the top level. Format-specific and kind-specific fields nest under a single `settings` object, and `format` and `kind` act as its discriminators. Create and update bodies take the same nesting.

A virtual repository's create and update bodies can carry an ordered list of upstream repository IDs, which states its upstreams after the write, in resolution order. It is the one kind-specific key outside `settings`, because no response returns it. It requires the upstream abilities of [ADR-021](021_authorization.md) as well as the repository ability, so it grants no write that the upstream routes would refuse.

Permission verdicts embed in the domain responses that carry the resources they gate, opt-in through a boolean query parameter. [ADR-021](021_authorization.md#permission-checks-for-ui-gating) defines the semantics, including which responses carry them.

##### Repository Deletion

Deleting a repository **requires** a destructive-intent query parameter that carries exactly `true` or `false`. It has no default: a request that omits it, or carries any other value, returns `400 Bad Request`. This ADR fixes the contract, not the parameter's name.

| Value   | Behavior                                                                                              |
|---------|-------------------------------------------------------------------------------------------------------|
| `false` | Deletes an empty repository and returns `204`, unless a virtual repository lists it as an upstream, in which case it returns `409 Conflict`. A repository that still holds artifacts returns `409 Conflict` |
| `true`  | Cascades: deletes the repository and its contents (`204` when already empty, `202` otherwise), unless a virtual repository lists it as an upstream, in which case it returns `409 Conflict`         |

Deleting an empty repository is synchronous and returns `204` under either value. The cascade against a non-empty repository is asynchronous: the request returns `202 Accepted`, the repository becomes unreachable at once (its name stays reserved until the deletion completes), and storage reclamation follows in the background.

The two values give two levels of protection: the caller declares destructive intent, and `false` still refuses to touch contents.

A repository that a virtual repository lists as an upstream returns `409 Conflict` under **either** value. Destructive intent does not reach it: the association is the virtual repository's configuration, not this repository's contents. The caller removes the association first. The `409` names the condition without listing the virtual repositories that hold the reference.

The parameter is required so that its removal fails loudly. GA makes soft delete the only delete path ([ADR-010](010_data_retention.md#release-phasing)), so the API drops the parameter, and a closed-beta integrator who still sends it gets an **explicit rejection that names the trash as the recovery path**, not a generic unknown-field `400`.

#### Repository-level APIs

Repository-level routes sit under `/api/v1/:slug/repositories/:repository_name`. Repository statistics and the remote connection test are format-free. Upstreams and lifecycle policies sit under the `:format` segment.

An upstream of a virtual repository references an existing hosted or remote repository, whose `kind` sets the upstream type. The upstream list follows resolution order. The upstream routes change one association at a time. The whole-list form on the repository body states the full list instead, and the registry applies it against the current set atomically.

Repository-level lifecycle policies override the namespace-level defaults.

#### Format-Specific Artifact APIs

Each format exposes its own artifact hierarchy under the `:format` segment: images and tags for the container family, and packages, versions, and files for Maven and npm.

Artifact routes are scoped to the repository. Routes, verbs, and pagination are the same for hosted and remote repositories. A route whose data the remote cache keeps as one document rather than per row, such as npm dist-tags, answers `404` on a remote repository.

Artifact responses are polymorphic by repository `kind`, like the repository `settings` object: a remote repository adds upstream freshness metadata to the rows that track it, and a hosted repository returns the same shape without it.

Verb semantics on a remote repository describe the cached row, not the upstream:

- `DELETE` evicts the cached row (no upstream effect; the artifact is re-fetched on the next pull through the client API).
- `PATCH .../quarantine` flags the cached row as blocked: client pulls return `404 Not Found` even if upstream still has the artifact. The flag follows the cached row's lifecycle, so eviction clears it. Persistent or digest-level blocks are out of scope, because they are a lifecycle-management concern, not an API one.
- `GET` is identical for both kinds, apart from that freshness metadata.

### Artifact Management Client APIs

Client API URLs are the same for all repository types (hosted, remote, virtual). The registry resolves the repository kind internally and applies type-specific behavior (e.g., rejecting writes on remote and virtual repositories, and refusing reads a repository kind cannot serve).

Each format implements its client protocol under `/:slug/:format/:repository_name/`. The container family is the one exception (see [Container](#container)).

#### Container

Implements [OCI Distribution Spec v1.1](https://github.com/opencontainers/distribution-spec/blob/main/spec.md). Authentication: [Bearer token](https://docs.docker.com/reference/api/registry/auth/).

Container routes live under `/v2/:slug/container/:repository_name/:image_name/`. The literal `container` path segment is fixed at the protocol level: one set of `/v2` endpoints serves repositories of both the `docker` and `oci` formats. It is a fixed literal, not the repository's `format` value (see [Management APIs](#management-apis)).

**Note:** The OCI-mandated `GET /v2/` endpoint has no `/:slug` prefix, so the [Cells](/handbook/engineering/architecture/design-documents/cells/) router cannot pick a Cell from its path. Any Cell can serve it, because it is a stateless version probe that answers `200 OK` for OCI compliance or `401 Unauthorized`. Every other client request carries a `/:slug` segment, which the Cells router uses to pick the target Cell. Clients get credentials through [`glab`](https://gitlab.com/gitlab-org/cli) (see [ADR-020](020_authentication_flow.md)) and send a Bearer token from the first request, so the registry never uses the OCI `401 WWW-Authenticate` challenge.

#### Maven

Implements [Maven Repository Layout](https://maven.apache.org/repositories/layout.html). Authentication: Basic auth.

#### NPM

Implements [NPM Registry API](https://github.com/npm/registry/blob/main/docs/REGISTRY-API.md). Authentication: Bearer token.

#### Go

Implements the [GOPROXY protocol](https://go.dev/ref/mod#goproxy-protocol) for reads, plus an upload route, because the protocol has no publish operation.

### GitLab API

The GitLab API serves platform callers, initially the Rails monolith. Requests authenticate the calling service, never an end user: user checks belong to the platform flows that trigger the calls, and user-facing traffic uses the management and client APIs instead ([ADR-014](014_frontend_to_artifact_registry.md), [ADR-021](021_authorization.md)). "GitLab" names the caller: a GitLab platform deployment, in the hybrid deployment model a customer-hosted monolith, so the surface is internet-facing yet never customer-facing.

[ADR-020](020_authentication_flow.md) and [ADR-021](021_authorization.md) cover how callers authenticate to this surface, including in the hybrid deployment model, where a Self-Managed or Dedicated monolith calls the SaaS registry.

#### Namespace Lifecycle

These endpoints are slug-exempt: provisioning runs before a slug is claimed, resolution turns a UUID into the slug, and service conditions must work regardless of the slug's state. They reference namespaces by owner anchor ([ADR-001](001_organizations_as_anchor_point.md)) or UUID ([ADR-022](022_namespace_decoupling.md)).

The platform provisions a namespace for an owner anchor and persists the namespace UUID it gets back. Provisioning is idempotent on the anchor. The platform resolves a namespace by UUID to its owner anchor, slug, and status, and caches the slug and status ([ADR-022](022_namespace_decoupling.md), [ADR-014](014_frontend_to_artifact_registry.md)). It applies and lifts the reversible service conditions of [ADR-022](022_namespace_decoupling.md#namespace-lifecycle) through one endpoint per action.

Slug-exempt routes do not weaken [Cells](/handbook/engineering/architecture/design-documents/cells/) routing. Namespace creation cannot be routed by key: nothing exists yet to route by. A cell-resident monolith calls its cell-local registry directly, and the namespace lands in that cell; a hybrid caller has no cell, so its call enters at the edge, which decides the target Cell. Both paths register the namespace UUID as a routing key, and the slug becomes a second key when claimed. All other GitLab API endpoints are keyed by that UUID and route through the same topology mechanism as slug-prefixed requests, wherever the caller sits. If UUID-keyed routing ever proves insufficient, GitLab API requests can also embed the owner anchor as a routing hint.

#### Resource Verifications

Platform authorization flows must confirm that resources targeted by bulk role grants belong to a namespace. Namespace-targeted grants need no registry call: the platform verifies ownership against its persisted mapping. Repository-targeted grants use a batch verification scoped by the namespace UUID. It succeeds only when every id belongs to the namespace, and otherwise lists exactly the failing ids without saying why one failed, so an id that exists nowhere and an id another namespace owns look the same.

The registry returns no organization data: the caller supplies the namespace scope and already knows its owner. Each future assignable resource type follows the same pattern, `POST /api/gitlab/v1/namespaces/:uuid/<resource_type>/verifications`.

The GitLab API must stay backward compatible across the platform versions it serves: in the hybrid deployment model, a Self-Managed monolith can lag the SaaS registry ([ADR-022](022_namespace_decoupling.md)).

## Consequences

### Positive

- **Clear separation of concerns**: The three API surfaces have distinct purposes, authentication mechanisms, and target audiences, reducing confusion and enabling independent evolution
- **Permanently stable, human-readable URLs**: Slugs and repository names are both immutable, so every URL path segment is human-readable and never changes. No numeric IDs appear in any client-facing URL
- **Unified hybrid list**: A single endpoint lists all repositories (hosted, virtual, remote) across all formats with filtering, enabling a cross-format governance and auditability view for platform engineers
- **Remote repositories as standalone entities**: Remote repositories are independently manageable, reusable across multiple virtual repositories, and have their own lifecycle, matching industry practice (JFrog Artifactory, Sonatype Nexus, Google Cloud AR)
- **Uniform hosted and remote artifact structure**: Remote repositories reuse the hosted artifact hierarchy, routes, and verbs, so API clients and the UI handle both kinds the same way
- **Simplified upstream model**: Virtual repository upstreams reference existing repositories by ID rather than using separate endpoint hierarchies per upstream type, reducing API surface and implementation complexity
- **API evolution outside the ADR**: Routes and payloads live in the OpenAPI and per-format specifications, so a new route or field needs no ADR change unless it breaks a rule here
- **Future extensibility**: The design accommodates additional package formats (PyPI, NuGet, Helm, etc.) without architectural changes. Management and Client APIs can evolve independently based on their respective requirements

### Negative

- **Repository name immutability limits flexibility**: A typo or organizational rename requires creating a new repository and migrating artifacts rather than simply renaming
- **Global name uniqueness is restrictive**: Names like `my-app` cannot be reused across formats (e.g., a Docker and a Maven repo both called `my-app`), which may lead to naming conventions like `my-app-docker` and `my-app-maven`
- **Format-specific API surface**: Dedicating endpoints per format means some duplication across formats and no unified cross-format operations for management tasks

## References

- [ADR-001: Organizations as Anchor Point](001_organizations_as_anchor_point.md)
- [ADR-010: Data Retention](010_data_retention.md#release-phasing) - Delete phasing across closed beta and GA
- [ADR-022: Namespace Decoupling](022_namespace_decoupling.md)
- [Cells Architecture](/handbook/engineering/architecture/design-documents/cells/)
- [Container Registry Routing Service (Cells)](https://gitlab.com/gitlab-com/content-sites/handbook/-/merge_requests/14825)
- [GitLab REST API Authentication](https://docs.gitlab.com/api/rest/authentication/)
- [OCI Distribution Spec v1.1](https://github.com/opencontainers/distribution-spec/blob/main/spec.md)
- [Docker Registry Bearer Token Authentication](https://docs.docker.com/reference/api/registry/auth/)
- [Maven Repository Layout](https://maven.apache.org/repositories/layout.html)
- [NPM Registry API](https://github.com/npm/registry/blob/main/docs/REGISTRY-API.md)
- [Repository Name Immutability Proposal](https://gitlab.com/gitlab-org/gitlab/-/issues/592582)
