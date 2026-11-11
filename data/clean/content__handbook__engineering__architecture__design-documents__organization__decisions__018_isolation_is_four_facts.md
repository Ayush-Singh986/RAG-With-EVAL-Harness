## Context

Today an Organization has one isolation setting,
`organization_isolations.isolated`, which is true or false. Code checks
it for three different reasons:

- To keep an Organization's Users from joining other Organizations.
- To block new links into or out of the Organization, such as outside
  members or MR dependencies.
- To decide whether the background validator checks the Organization's
  data. When the validator finds a cross-Organization link, it sets
  `isolated = false`.

One setting cannot serve all three. For example, an owner who wants to
try blocking new links before committing must set `isolated = true`,
which also locks their Users into the Organization. Docs share the
problem: [Request Context](../contexts.md) and
[ADR 016](016_user_context.md) say "isolated" without saying which
meaning.

## Decision

Isolation is four independent facts. Docs and code always say which one
they mean, for example "enforced isolation" rather than "isolation."

| Term | Means | Reversible |
|------|-------|------------|
| **Requested isolation** | The owner has asked to isolate, which starts severance. | Until committed |
| **Enforced isolation** | GitLab blocks writes that would create new cross-Organization links. | Until committed |
| **Committed isolation** | The owner has committed, and severance has completed. | No |
| **Verified isolation** | The background validator found no cross-Organization links. | Lapses on drift |

Committed isolation requires requested and enforced isolation. Enforced
isolation stays on from commitment onward.

The table below shows example rules, one or more per fact. It is a
sample, not a complete list: many more rules depend on isolation, and
each one names the fact it reads.

| Example rule | Reads |
|--------------|-------|
| Starting severance | Requested isolation |
| Blocking new cross-Organization links: outside members, MR dependencies, imports | Enforced isolation |
| Organization context ([Request Context](../contexts.md)) | Committed isolation |
| Exclusive membership and `organization_id` reassignment ([ADR 016](016_user_context.md)) | Committed isolation |
| Organization filter on Organization-scoped finders ([ADR 016](016_user_context.md)) | Committed isolation |
| Reporting drift to the owner, naming the link to fix | Verified isolation |
| Moving to another Cell | Committed and verified isolation |

## Consequences

1. An owner can turn on enforced isolation to try it out, then turn it
   off again. Membership, User context, and query filtering do not change.
1. When the validator finds a new cross-Organization link, only verified
   isolation lapses. Committed isolation stays, so the Organization keeps
   Organization context, exclusive membership, and the Organization
   filter while the owner fixes the link.
1. Each `isolated?` caller moves to the fact it means.

## Alternatives considered

1. **One boolean**: forces preview, severance, and drift to share one
   answer.
1. **Isolation levels** (Fully, Resource, or Not Isolated): describe
   only how much data is contained, which is verified isolation alone.
1. **Merging committed into verified isolation**: drift would undo a
   one-way decision.
