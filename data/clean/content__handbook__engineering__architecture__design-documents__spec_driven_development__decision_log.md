Read more about SDD in [Spec-Driven Development](_index.md).

**Maturity: Still defining**

## Summary

The decision log is a record of the decisions made about a work item. It keeps the reason for each decision next to the work item, so the history is not lost in chat or in comment threads. Humans and agents both read it and write to it.

When a complex work item needs a lot of alignment, pending questions get lost, and adding every resolved decision to the description makes it too long. Someone who joins later spends a long time catching up. With agents, collaboration moves faster, and humans and other agents need to see the decisions made in conversations between humans and agents.

For this iteration, the decision log is not a long-lived artifact. Its lifespan is tied to the work item.

Epic: [WS-5: Decision log](https://gitlab.com/groups/gitlab-org/-/work_items/21552)

User documentation: [Decision log](https://docs.gitlab.com/user/work_items/workplan/#decision-log)

## Scope

- Available on issues and tasks, and on custom work item types based on them.
- A work item does not need a Workplan or AI planning to have a decision log.
- Viewing and recording decisions is available to the Planner, Reporter, Security Manager, Developer, Maintainer, and Owner roles. A stricter permission model is still being discussed.
- The decision log opens in a side panel from the work item header. The header button counts resolved, non-archived decisions. Open decisions are stored but hidden from the panel for this iteration ([issue 631883](https://gitlab.com/gitlab-org/gitlab/-/work_items/631883)).

## Data model

Decisions are stored in their own tables, `work_item_decisions` and `work_item_decision_options`, joined to the work item. The backend work is tracked in the [data model and backend epic](https://gitlab.com/groups/gitlab-org/-/work_items/22374).

The existing model derives a decision's state from its timestamps:

- `active`: An open decision, with no resolution or archive timestamp.
- `resolved`: A decision with a resolution timestamp and no archive timestamp.
- `archived`: A decision with an archive timestamp.

This lifecycle supports creating an open question with options and resolving it later. A decision can also be created already resolved to record an outcome directly.

The API and model use `question` for the question a decision answers. Create and update mutations accept it alongside the legacy `title` argument during the transition ([merge request 259900](https://gitlab.com/gitlab-org/gitlab/-/merge_requests/259900)). The database column rename is a separate follow-up.

## Interactions

First iteration, tracked in the [frontend epic](https://gitlab.com/groups/gitlab-org/-/work_items/22375):

- Record a decision manually. Required fields are the decision, who decided, and the context. Optional fields are the reasoning and a source link.
- Show each decision as a card with the decision, the open question it answers, who settled it and when, where it came from, and the context and reasoning.
- Link a decision to the thread and comment that produced it.
- Edit the decision text and decider, delete a decision, or archive it. Archived decisions can be shown with a visibility toggle.
- Resolving a Duo question through the work item UI resolves its matching decision. A general action to resolve any thread by creating or picking a decision is still tracked in [issue 603073](https://gitlab.com/gitlab-org/gitlab/-/work_items/603073).
- A decision quick action and a resolve-with-decision option are proposed in [issue 634656](https://gitlab.com/gitlab-org/gitlab/-/work_items/634656). The proposal is still under discussion and not yet decided. The current direction in that issue is that creating a decision from a thread should not have to resolve the thread, because one thread can produce several decisions.
- Recording or resolving a decision creates an activity-feed system note linking directly to its card. The note follows the decision log's visibility rules ([merge request 259191](https://gitlab.com/gitlab-org/gitlab/-/merge_requests/259191)).
- A link to an archived decision turns on the archived visibility toggle and scrolls the card into view. A link to a decision that does not exist shows a dismissible warning, and the other decisions still show ([merge request 263112](https://gitlab.com/gitlab-org/gitlab/-/merge_requests/263112)).

Deferred to a later iteration:

- An approval lifecycle beyond the existing active, resolved, and archived states, including negative decisions.
- Decision assignees and the to-do items they create.
- Cascading decisions from child work items up to the root epic.
- Decision categories, ordering, and superseding a decision.

## Agents

- The backend creates an open decision when the workplan flow's service account posts a valid clarifying question. It stores the question, options, discussion, and workflow reference.
- The frontend resolves the matching decision when the user resolves the question thread through the work item UI. This requires the decision log to be available on the work item. See [Human in the loop](human-in-the-loop.md#relationship-to-the-decision-log) for failure handling and older questions.

## Observability

Internal events track a decision being recorded as already resolved, an open decision being resolved, and the decision-log panel being opened. Resolution events include how the decision was settled. Creating an open question alone is not counted as a resolved decision ([merge request 261013](https://gitlab.com/gitlab-org/gitlab/-/merge_requests/261013)).

Editing, archiving, and deleting an open decision also send events. They carry the work item, the decision, and the request source: the web UI, the API, or an AI workflow ([merge request 263772](https://gitlab.com/gitlab-org/gitlab/-/merge_requests/263772)). The panel view event carries the work item ID and whether the panel was opened from a deep link or the header button ([merge request 264363](https://gitlab.com/gitlab-org/gitlab/-/merge_requests/264363)).

## Decisions

| Date | Decision | Who |
| ---- | -------- | --- |
| 2026-09-09 | The decision log is independent of the Workplan and of AI planning. Its rendering is split from the AI planning widget ([issue 624791](https://gitlab.com/gitlab-org/gitlab/-/work_items/624791)). | WS-5 |
| 2026-09-15 | The decision log can be offered in the Free tier, but this is not a priority ([issue 628417](https://gitlab.com/gitlab-org/gitlab/-/work_items/628417)). Until then, it stays behind the `ai_workflows` licensed feature. | @gweaver, @nickbrandt |

## Open questions

- How to expose open decisions and their options in the panel ([issue 631615](https://gitlab.com/gitlab-org/gitlab/-/work_items/631615)).
- Whether reopening a resolved decision should modify it in place or supersede it ([issue 632762](https://gitlab.com/gitlab-org/gitlab/-/work_items/632762)).
- Requiring both work-item update permission and internal-note access, including behavior on archived projects ([issue 632270](https://gitlab.com/gitlab-org/gitlab/-/work_items/632270)).
