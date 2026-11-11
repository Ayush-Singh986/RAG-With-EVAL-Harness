## Context

The original proposal listed a `RebaseMergeRequestService` responsible for
rebasing open dependency update merge requests when they hit a merge
conflict. That service was never built.

Rebasing turned out to be the wrong operation. A dependency update merge
request that conflicts with its target branch has usually conflicted
*because the manifest or lock file moved underneath it* — exactly the input
the resolver needs in order to reconsider. A rebase would replay a stale
resolution onto new state. It also would not help the adjacent case, where
the merge request merges cleanly but a newer patched version has since been
published.

## Decision

We re-run the update workload instead of rebasing the branch. Before
scanning for new work, the scheduler walks the merge requests it already has
open and re-runs the update for the ones that need it. Because the update
commits to the merge request's existing source branch and updates the
existing merge request rather than opening a new one, the refresh lands in
place — no new branch, no new merge request, review history preserved.

An open merge request is refreshed in two cases:

1. **Its refresh cooldown has elapsed**, so a newer patched version can reach
   the open merge request. Gating on a cooldown is what keeps this from
   running a workload on every pipeline.
1. **It is recorded as conflicted** and both branches still exist. Nothing
   else recovers this state: the branch writes bypass the mergeability
   recheck that a normal push triggers, and there is no periodic sweep. This
   case does not wait for the refresh cooldown, because a conflicted merge
   request stays stuck until something refreshes it. With the hidden
   workload ref described below, it is limited instead to one refresh per
   branch head for the length of the refresh cooldown. A refresh whose
   workload does not commit leaves the head as it was, so without the limit
   every pipeline would start another workload. A commit moves the head and
   frees the next attempt. So does a refresh that skips its commit because
   the merge request already holds the output, since it is then not
   conflicted. A refresh from the first case that does not commit holds the
   head the same way. If the limit cannot be checked, the refresh is skipped
   rather than run on every pipeline.

The workload runs on a hidden ref at the target branch's tip, so a refresh
leaves the merge request's branch untouched until it has a result to commit.
The first implementation reset the branch to the target before the workload
ran. That recorded an empty diff version, reset approvals on every refresh
where the project resets them on push, and was also what ended a conflict
after a single attempt. The hidden ref and the conflict limit are behind the
`dependency_management_workload_ref_refresh` feature flag, tracked in the
[workload ref rollout issue](https://gitlab.com/gitlab-org/gitlab/-/work_items/633463).

Refreshing up front, rather than whenever the scan happens to encounter the
component again, also keeps the open-merge-request accounting in
[001](./001_bounded_severity_prioritized_remediation.md) correct. A
vulnerability can be dismissed, resolved, or fall outside the configured
severity threshold and so never reappear in the scan, which would otherwise
stop the scan from terminating early once the limit is reached.

## References

1. `ee/app/services/dependency_management/security_update/scheduler_service.rb`
1. `ee/app/services/dependency_management/security_update/refresh_cooldown.rb`
1. `ee/app/services/dependency_management/security_update/create_merge_request_service.rb`
1. `ee/app/services/dependency_management/security_update/update_service.rb`
1. [001: Bounded, severity-prioritized remediation](./001_bounded_severity_prioritized_remediation.md)
1. [004: Package release cooldown](./004_package_release_cooldown.md)
