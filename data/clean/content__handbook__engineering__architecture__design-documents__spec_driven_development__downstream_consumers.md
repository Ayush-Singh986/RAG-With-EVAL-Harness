Read more about SDD in [Spec-Driven Development](_index.md).

**Maturity: Still defining**

## Summary

The Workplan's value comes from being consumed by downstream agents. This page covers how Duo Developer implements a Workplan, and how validation against the Workplan could work later.

## Duo Developer handoff

When a Workplan exists, a user selects **Implement** on the Implementation widget or in the Workplan panel. This starts the Duo Developer flow (`developer/v1`) asynchronously, without opening Duo Chat ([issue 628801](https://gitlab.com/gitlab-org/gitlab/-/work_items/628801)).

Duo Developer treats the Workplan as the primary specification. It uses the work item description and comments only for additional context. It also treats every point in the [readiness](readiness.md) feedback, including non-blocking ones, as a finding to resolve. For each point, it either resolves it or explains in the merge request description why it did not ([merge request 265980](https://gitlab.com/gitlab-org/gitlab/-/merge_requests/265980)).

Prerequisites: Duo Agent Platform remote flows must be enabled. When the Developer flow is not configured, the **Implement** button is disabled with a tooltip ([issue 629904](https://gitlab.com/gitlab-org/gitlab/-/work_items/629904)).

The **Implement** button is hidden on closed work items in both the widget and the Workplan panel ([merge request 261747](https://gitlab.com/gitlab-org/gitlab/-/merge_requests/261747)). Starting the Developer flow also requires the CI flow permission; aligning it with work-item action permissions is tracked in [issue 634208](https://gitlab.com/gitlab-org/gitlab/-/work_items/634208).

Showing the implementation phase and the merge request status on the Implementation widget remains open in [issue 628976](https://gitlab.com/gitlab-org/gitlab/-/work_items/628976). Handling repeated **Implement** clicks while a run is active, while still allowing an intentional restart, is part of that ongoing design work.

## Duo Review validation (deferred)

The Duo Review agent could validate merge request changes against the originating Workplan, using it as evaluation criteria. This depends on the [work item to merge request relationship](wi_mr_relationship.md). It is not part of the current epic.

Epic: [Workstream 1: MR spec enforcement](https://gitlab.com/groups/gitlab-org/-/work_items/21514)

## Merge check in MR (deferred)

Validating the Workplan at merge time as a merge check is not part of the current epic. It may be covered by the [Code Review Lifecycle Transformation](https://docs.google.com/document/d/1BsdLonLqNyB0QSdEiUaJJ5GNQLkr-gKx_uQNTApdfCA/edit?tab=t.0) initiative instead of SDD.

## API surface

Downstream agents read the Workplan through the work item GraphQL API and the MCP work item tools. See [Workplan](workplan.md#api-surface).

## Structured vs raw Markdown

Downstream agents consume the Workplan as raw Markdown. If the Workplan evolves to a richer structure, such as sections, acceptance criteria, or test cases, serialization and backward compatibility will need to be addressed.

## Decisions

| Date | Decision | Who |
| ---- | -------- | --- |
| 2026-04-17 | The Workplan format consumed by downstream agents is **Markdown** (not YAML or structured JSON). Markdown is human-readable, already the common format of GitLab descriptions, and avoids serialization overhead for consumers. | @fredericcaplette |
| 2026-09-23 | **Implement** runs Duo Developer asynchronously instead of opening Duo Chat. | WS-7 |
