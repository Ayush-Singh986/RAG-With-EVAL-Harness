## Overview

Stable branches are the source of the GitLab release packages delivered to GitLab customers. They serve
as a foundation for versioned releases, and it is fundamental that they remain reliable for any GitLab
release process (monthly, patch or internal).

## Principles

- At GitLab, it is everyone's responsibility to keep stable branches green and reliable. Similar to master branch failures, addressing stable branch failures takes priority over everything else development-related.
- Stable branches receive bug fixes and security patches according to the [maintenance policy](https://docs.gitlab.com/policy/maintenance/).
- Stable branches can also receive upkeeping efforts & catch-up corrective improvements (performance improvements, documentation updates, spec fixes, etc).

## Workflow

1. Stable branches are created when the initial release candidate of a monthly release is tagged.
1. After creation, stable branches are automatically propagated to [security](https://gitlab.com/gitlab-org/security) and [dev](https://dev.gitlab.org/) repositories through repository mirroring.
1. Bug and security fixes are [backported](/handbook/engineering/releases/backports) to stable branches based on the [maintenance policy](https://docs.gitlab.com/policy/maintenance/).
1. Changes backported to stable branches are automatically deployed to [release environments](https://gitlab.com/gitlab-com/gl-infra/release-environments) to guarantee they're compatible with the GitLab version.
1. Patch and internal releases are created from the content of stable branches.

## Characteristics

- Stable branch permissions are based on the [maintenance policy](https://docs.gitlab.com/policy/maintenance/). Stable branches associated with
the [maintained versions](https://docs.gitlab.com/policy/maintenance/#maintained-versions) are opened to GitLab maintainers for merging while older stable branches are limited to Release Managers.
- To account for security fixes and [release environments](https://gitlab.com/gitlab-com/gl-infra/release-environments), security repositories represent the SSOT for stable branches.
- Tests on stable branches are the same on canonical and security repositories, with the exception of release environments that are only available on the GitLab security repository.

## Build Infrastructure

Release artifacts are built from mirrored repositories using dedicated CI runner infrastructure.
For a full description of which mirrors exist, what builds where, and the rationale behind this architecture, see the
[Build Infrastructure documentation](../infrastructure-platforms/gitlab-delivery/build-infrastructure.md).

## Broken Stable Branches

When a stable branch pipeline fails, triage-ops opens an incident in [gitlab-org/release/tasks](https://gitlab.com/gitlab-org/release/tasks) and posts it to `#releases`. Release managers watch these incidents, because a broken stable branch can block patch and security releases. These incidents are not CI Health incidents and are not escalated automatically.

To triage or fix the failure, follow the steps in [If you're assigned to an incident](/handbook/engineering/workflow/#triage-broken-master).
