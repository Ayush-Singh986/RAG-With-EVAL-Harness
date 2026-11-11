This guide covers the Zendesk apps currently used in the Global Zendesk instance.

## Advanced SAST App

<sup>*Introduced via [support-team-meta#6652](https://gitlab.com/gitlab-com/support/support-team-meta/-/issues/6652)*</sup>

The Advanced SAST App is a ticket app that enables a quick working of User requests for source code of LGPL-licensed components in GitLab Advanced SAST.

- Location: Ticket sidebar
- Restricted by Group:
  - Support AMER
  - Support APAC
  - Support EMEA
- This application was developed in-house and can be found [Advanced SAST App project](https://gitlab.com/gitlab-support-readiness/zendesk-global/apps/advanced-sast-app).

## Advanced Search

Advanced Search is an app that provides a simple visual interface for constructing complex search queries against tickets, users, and organizations (orgs). It also enables you to export the search results in a CSV format.

- Location: Navbar
- This application was developed by [Zendesk](https://www.zendesk.com/marketplace/partners/zendesk/) and is available in the [Zendesk Marketplace](https://www.zendesk.com/marketplace/apps/support/198393/advanced-search/).

## Contact Management

<sup>*Introduced via [gitlab-com/eta/css/issue-tracker#7](https://gitlab.com/gitlab-com/eta/css/issue-tracker/-/work_items/7)*</sup>

This application is used for managing support contacts in Zendesk Global. Its functionality depends on the requester's association status and product type:

- For unassociated users:
  - If the `L&R Product Type` is `GitLab.com`:
    - It can attempt auto-association. This is done by reviewing the requester's gitlab.com account to locate the top-level paid namespaces it is an Owner of (and locating the corresponding organization tied to it via the Salesforce Account).
  - If the `L&R Product Type` is `Self-Managed` or `GitLab Dedicated`:
    - Associate users to an organization (via the Salesforce Account). It will ask for the needed information, add an internal note, and make any changes it is able to make.
- For associated users:
  - It can list the support contacts for the requester's organization
  - It can add users to the requester's organization
  - It can remove users from the requester's organization

All end-user changes the app performs will add a message on the `Details` attribute of the modified end-user to indicate the organization, ticket, and agent.

Do note the app will not circumvent policy restrictions, such as:

- Performing actions outside of tickets using the form `Support Ops`
- Exceeding the 30 support contact maximum limit
- Modifying support contacts for organizations using contact management projects

- Location: Ticket sidebar
- Restricted by Group:
  - Support Ops
  - ASEs
- This application was developed in-house and can be found [Contact Management project](https://gitlab.com/gitlab-support-readiness/zendesk-global/apps/contact-management).

## GitLab Reminders App

<sup>*Introduced via [support-team-meta#3036](https://gitlab.com/gitlab-com/support/support-team-meta/-/issues/3036)*</sup>

The Reminders App appears in the navbar and allows the agent a more specialized view of tickets they are involved in. It currently shows:

- Tickets assigned to you with a pending/overdue task that are not in a Closed state
- Recent tickets you have viewed
- Tickets assigned to you that are not in a Closed state
- Tickets you are following that are not in a Closed state

It also allows you to quickly manage your tasks by seeing the notes you have left for said task, when it is due, and a button to quickly mark the task as done (remove the notes and due date).

- Location: Navbar
- This application was developed in-house and can be found [GitLab Reminders App project](https://gitlab.com/gitlab-support-readiness/zendesk-global/apps/reminders-app).

## GitLab Super App

<sup>*Introduced via [support-team-meta#801](https://gitlab.com/gitlab-com/support/support-team-meta/-/issues/801)*</sup>

A plugin controlled app that can do several things GitLab related

The current plugins are:

- User Lookup
  > This lets you search gitlab.com for a username or email. It then displays information based on the results.
- Namespace Lookup
  > This lets you search gitlab.com for a namespace. It then displays information based on the results.
- Collaboration Project
This checks the organization for a collaboration project ID. If one exists, it then provides a link to said project.
- Email Suppressions
  > This searches mailgun for suppressions from bounces (note it does not do it on complaints or unsubscribes). It will display the results (with the message for the suppression).
  >
  > It also gives the option of removing the suppression (if one if found). Doing so deletes it from mailgun and adds an intenral comment on the ticket with the results of the suppression deletion.
- Fieldnotes
  > This app checks the [Fieldnotes project](https://gitlab.com/gitlab-com/support/fieldnotes/-/issues) for any existing Issues which reference the current Zendesk ticket ID. If no existing Issues are found, then agents are able to create a new Fieldnotes Issue from directly within the Zendesk ticket.
- Account Verification Helper
  > This creates a usable form to check if an account verification has passed based on the type of verification selected. It calculates the Risk Factor from the challenges passed and modifies it to reflect the passed challenges. It also allows for posting an internal note of what the form reflects.

- Location: Ticket sidebar
- Restricted by Group:
  - BPO
  - Support AMER
  - Support APAC
  - Support EMEA
- This application was developed in-house and can be found [GitLab Super App project](https://gitlab.com/gitlab-support-readiness/zendesk-global/apps/gitlab-super-app).

## Glean

<sup>*Introduced via [issue-tracker#798](https://gitlab.com/gitlab-com/gl-security/corp/cust-support-ops/issue-tracker/-/work_items/798)*</sup>

Glean connects to and understands all your company's knowledge to bring you the answers you need while working in Zendesk. With Glean, teams improve customer experience with faster response times using state-of-the-art enterprise search and RAG technology to retrieve the most relevant, up-to-date information. Whether it is accessing ticket context, product experts, or customer information to respond to questions and unblock issues quickly, Glean generates highly personalized answers grounded in your company's unique enterprise knowledge graph.

Through Glean you can:

- Get a summary of the ticket
- Get suggested next steps
- Draft a response
- Perform a search across GitLab resources
- Use GitLab pre-defined prompts

- Locations:
  - Navbar
  - Ticket sidebar
- Restricted by Group:
  - Accounts Receivable
  - Billing
  - BPO
  - Support AMER
  - Support APAC
  - Support EMEA
- This application was developed by Glean and is available in the [Zendesk Marketplace](https://www.zendesk.com/marketplace/apps/support/922191/glean/).

## STAR

<sup>*Introduced via [support-team-meta#4694](https://gitlab.com/gitlab-com/support/support-team-meta/-/work_items/4694)*</sup>

Support Ticket Attention Requests (STAR) are the mechanism by which GitLab Team Members can request additional attention be placed on tickets. This is the app agents use in Zendesk to start a STAR process.

- Location: Ticket sidebar
- This application was developed in-house and can be found [STAR project](https://gitlab.com/gitlab-support-readiness/zendesk-global/apps/star).

## Zendesk Super App

<sup>*Introduced via [support-ops-project#801](https://gitlab.com/gitlab-com/support/support-ops/support-ops-project/-/issues/801)*</sup>

A plugin controlled app that can do several things Zendesk related

- Create new ticket
  > Allows an agent to create a new ticket using the same user as the ticket they are currently on.
- Due date picker
  > This allows you to customize what the Due Date for a Task ticket is set for. By default, Zendesk only allows setting the date. This enables you to set the date, time, and timezone.
  >
  > You can also set the Due Date Note and disable (or enable) task notifications using this app.
- Escalated tickets
  > This searches for tickets under the organization that have been escalated within the last 6 months.
- Related tickets
  > This looks for tickets related to the current one based off the category (or subcategory) the ticket is currently using. It then displays up to 5 of them (sorted by the update_at value of the ticket, descending).
- Attachments
  > Displays attachments present on the ticket.

- Location: Ticket sidebar
- Restricted by Group:
  - BPO
  - Support AMER
  - Support APAC
  - Support EMEA
- This application was developed in-house and can be found [Zendesk Super App project](https://gitlab.com/gitlab-support-readiness/zendesk-global/apps/zendesk-super-app).

## ZenGuard

<sup>*Introduced via [issue-tracker#122](https://gitlab.com/gitlab-com/gl-security/corp/cust-support-ops/issue-tracker/-/issues/122)*</sup>

Implements a warning system into Zendesk to warn (or block) potentially dangerous actions. If a warning is bypassable, then a close button (X) appears to the right of it (and clicking said button removes the warning).

Current list of checks:

- Checks if making unapproved form changes

- Location: Ticket sidebar
- This application was developed in-house and can be found [ZenGuard project](https://gitlab.com/gitlab-support-readiness/zendesk-global/apps/zenguard).
