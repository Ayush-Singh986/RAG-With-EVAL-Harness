Read more about SDD in [Spec-Driven Development](_index.md).

**Maturity: Still defining**

## Summary

When the [async workplan flow](workplan-flow.md) hits a decision it should not make alone, it asks a clarifying question in the work item discussions. A human answers there, and the flow picks up the answer and continues. Examples are whether something is free or paid, who can see it, or whether a change breaks existing behavior. A plan built on a wrong guess is worse than no plan.

Epic: [WS-4: HITL and notifications](https://gitlab.com/groups/gitlab-org/-/work_items/22772)

Designs: [SDD iteration path in Figma](https://www.figma.com/design/uJb85wjoRaj7MMvjxAmdHf/SDD-Iteration-Path?node-id=46-27205)

## Why work item discussions

- A question in a discussion is durable. A chat session is not.
- Other people can see the question and weigh in.
- The work item already holds everything else about the work, so the decision sits next to what it affects.
- Any flow that needs to ask something can use the same surface, not only workplan generation.

## Interaction

1. The flow posts a comment with its question and attaches a small machine-readable payload that describes the question, the options, and its recommendation.
1. The work item renders the question as a card in the thread. The card shows up to five options and which one the flow recommends. Cards render only for notes authored by the Duo bot. They don't depend on the `workplan` feature flag: a valid question payload renders as a card, including in board drawers. A question posted while the flag was on stays answerable after the flag is turned off, while generating and resuming stay blocked by the backend ([merge request 264177](https://gitlab.com/gitlab-org/gitlab/-/merge_requests/264177)).
1. A user answers by choosing an option. Some questions accept more than one answer. A user can also give a free-text answer.
1. If none of the options are right, a user can reject them. An explanation is required, because that is what the flow acts on next.
1. Answering posts the choice as an ordinary reply and resolves the thread. The thread is resolved only if the user has permission to resolve it. The chosen answers remain visible; options that were not selected can be expanded in a disabled state after resolution ([merge request 260428](https://gitlab.com/gitlab-org/gitlab/-/merge_requests/260428)).
1. The user selects **Continue** on the Implementation widget to resume the flow with the answers and open the session in the Duo drawer.

Permission to resume and eligibility to supply answers are separate. The resume service checks work-item update permission and project remote-flow availability, then uses the original flow owner's identity. Starting a new CI flow has a separate Developer-level permission check; aligning the role policy is tracked in [issue 634208](https://gitlab.com/gitlab-org/gitlab/-/work_items/634208). The resume service includes replies only from users with a project role above Guest. Replies from Guest and lower roles are excluded, even when the author can update the work item and select **Continue**.

Thread resolution is not required to resume. The service collects eligible replies to question payloads from both resolved and unresolved threads. Unanswered questions do not block a resume; if there are no eligible replies, the flow is instructed to continue with its best assumptions. A request to expand the description follows a separate path: the user edits the description, and **Continue** resumes research with the original goal.

Because the answer is a normal comment and a normal thread resolution, everything stays visible. The payload is stripped from note emails.

## Question navigation

While a flow awaits input, the Implementation widget shows its open-question count and previous/next navigation. The sticky header also exposes question navigation. Resolved threads are skipped, and answering from a card refreshes the widget without waiting for its next poll ([issue 608855](https://gitlab.com/gitlab-org/gitlab/-/work_items/608855), [issue 628347](https://gitlab.com/gitlab-org/gitlab/-/work_items/628347), and [issue 631032](https://gitlab.com/gitlab-org/gitlab/-/work_items/631032)).

The backend counts unresolved flow-note threads across all runs, while navigation filters for question payloads. Progress notes and context requests can therefore inflate the count. A Guest can also resolve a thread whose reply is excluded from the resume goal. The counter is a navigation aid, not an authorization check or a prerequisite for resuming.

## Notifications

When the flow pauses for input, the user is notified. This was implemented in the AI Gateway in [merge request 6711](https://gitlab.com/gitlab-org/modelops/applied-ml/code-suggestions/ai-assist/-/merge_requests/6711).

## Relationship to the decision log

Automatic recording of clarifying questions and their answers in the [decision log](decision_log.md) is implemented in two parts:

1. The backend creates an open decision with the question, options, and discussion ID when the flow posts a clarifying question ([issue 630439](https://gitlab.com/gitlab-org/gitlab/-/work_items/630439)).
1. The frontend resolves that decision when the thread is resolved through the work item UI, recording the selected options or free-text rationale and linking the answer reply ([merge request 259195](https://gitlab.com/gitlab-org/gitlab/-/merge_requests/259195)).

This integration requires the decision log to be available for the work item's license and type. If no matching decision exists, such as for an older question, the frontend skips recording. Resolving without an answer records a fixed rationale rather than selecting an option. Reopening and resolving the thread again does not replace the first decision resolution. Resolving a thread outside this UI does not automatically resolve its decision.

Open decisions are stored but hidden from the decision-log panel until resolved. Recording a decision is separate from resuming the flow: **Continue** does not resolve threads or decisions, and a decision-log mutation failure does not prevent the answer from being posted.

## Open questions

- **Approval requests**: A single run can produce real questions and requests to approve a tool call. The current thinking is that discussions carry questions only, and approvals stay where the person running the flow can see them.
- **Updating the spec**: Automatically updating the description from a resolved Duo decision is in development ([issue 633224](https://gitlab.com/gitlab-org/gitlab/-/work_items/633224)). A backend service that applies an AI-generated description update from a resolved Duo decision exists. It strips quick actions and escapes new mentions, but nothing calls it yet ([merge request 262147](https://gitlab.com/gitlab-org/gitlab/-/merge_requests/262147)). The proposed backend event and worker that trigger it and link the description version to the decision are still open. The frontend diff presentation and whether manual decisions should also update the description remain under discussion in [issue 629471](https://gitlab.com/gitlab-org/gitlab/-/work_items/629471).
- **Unanswered questions**: The flow waits for an explicit **Continue** action, which can resume it without answers. Nothing chases an unanswered question or cleans it up.
- **Resolving without replies**: The work item UI can resolve a discussion before anyone replies. It shows the collapsed reply box with a **Resolve thread** button, and the **Resolve thread** checkbox in the reply form ([merge request 259967](https://gitlab.com/gitlab-org/gitlab/-/merge_requests/259967), [merge request 263718](https://gitlab.com/gitlab-org/gitlab/-/merge_requests/263718)). Plain comments still become resolvable only after a reply, and the flow currently posts plain comments. Posting discussions directly is tracked in [issue 633575](https://gitlab.com/gitlab-org/gitlab/-/work_items/633575). This is a prerequisite for [Resolve all questions](https://gitlab.com/gitlab-org/gitlab/-/work_items/631563).
- **Answer eligibility**: Aligning resolved-question counts with the resume service's reply permissions ([issue 631546](https://gitlab.com/gitlab-org/gitlab/-/work_items/631546)).
