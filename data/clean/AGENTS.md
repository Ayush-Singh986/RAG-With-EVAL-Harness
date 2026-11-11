# GitLab Handbook Projects - Agent Instructions

## Identify the repository first

1. Run `git rev-parse --show-toplevel` and inspect `git remote -v` to identify the
   checkout and its upstream project. Do not infer the project from the directory name:
   parent directories can contain several repositories, and worktrees can have arbitrary names.
1. Match the upstream project below. For a fork, inspect its upstream remote and repository
   files. If the identity remains unclear, establish it before applying project-specific rules.
1. Read the shared instructions, then the matching section at the bottom of this file.
   Check for additional `AGENTS.md` files in the directories you will edit.
1. Before planning or editing, read `.gitlab/duo/mr-review-instructions.yaml` from the repository
   root. This is the authoritative review checklist; use it as acceptance criteria throughout the task.

| Upstream project under `gitlab-com/content-sites` | Instruction path |
| --- | --- |
| `docsy-gitlab` | [Docsy GitLab](#docsy-gitlab) |
| `handbook` | [Public handbook](#public-handbook) |
| `internal-handbook` | [Internal handbook and SAFE](#internal-handbook-and-safe) |

## Shared repository map

- `content/` contains Markdown pages. Its meaning differs by project; see the selected path below.
- `assets/includes/` contains reusable Markdown where present.
- `assets/`, `layouts/`, `data/`, and `config/` contain site assets, templates, and configuration.
- `config/_default/config.yaml` contains site settings and navigation.
- `scripts/` contains synchronization, maintenance, and CI helpers.
- `go.mod` records Hugo module dependencies.
- `public/` and generated files in `resources/` are build output.

## Content and change discipline

The [Handbook Markdown guide](https://gitlab.com/gitlab-com/content-sites/docsy-gitlab/-/blob/main/content/docs/markdown-guide/index.md)
is the canonical source for formatting. Follow it over conflicting formatting summaries here.

- Check `git status` before and after work. Preserve unrelated changes and generated artifacts.
- Search with `rg` before editing. For tracked files, fall back to `git grep` and `git ls-files`;
  use `grep` or `find` when untracked files must be included.
- Locate the canonical page and inspect adjacent pages, front matter, and referenced includes.
  Preserve organization, terminology, heading hierarchy, and local style; avoid broad reformatting.
- Check `.gitlab/CODEOWNERS` before ownership-sensitive or controlled-document changes.
  Preserve required owners and approval groups. Do not invent policies, owners, dates, or approvals.
- Update the source include rather than duplicating its content. Use `assets/includes/` only when
  multiple pages need the same text.
- Use numbered lists for sequences and bullets for independent items. The guide recommends
  ordered lists for referenceability but supports both styles.
- Write concise Markdown with descriptive inline links. Leave blank lines between block elements,
  use fenced code blocks with a language, and do not skip heading levels. Start Hugo page content
  at `##` because the page title supplies `#`; standalone documents may have their own `#` title.
- Add meaningful image alternative text and use lowercase, hyphenated filenames for new content.
  Preserve Hugo shortcodes and follow nearby examples.
- Preserve front matter unless the task requires a change. New Hugo pages need `title` and `description`;
  follow the closest sibling, use ISO 8601 dates, and check for duplicate or misspelled keys.
- Keep heading anchors stable where possible. For changed paths or anchors, update incoming links
  and assess redirects. Preview shortcode, image, table, and navigation changes in rendered context.
- Do not hand-edit synchronized files, especially `data/public/`; use `scripts/sync-data.sh`.
- Never commit secrets, local paths, temporary module replacements, or generated output.
- Update dependencies individually and pin released versions; never select `latest`.

## Rename handbook paths

Use `skills/handbook-path-rename/SKILL.md` when moving or renaming handbook pages or
sections. Apply this checklist even when the skill is unavailable:

1. Move the content and page resources together; preserve meaningful heading anchors.
1. Add old-to-new redirects in `layouts/index.redirects`. Do not add Hugo `aliases`.
   Group related entries under `# <description> - remove YYYY-MM-DD`, ordered by removal
   date. For moves within one handbook, use three calendar months from the change date.
   Use exact redirects for partial moves; use a subtree wildcard only when every page moves.
1. Update incoming and relative links, landing pages, `data/toc.yaml` where present,
   includes, scripts, automated comments, and affected `.gitlab/CODEOWNERS` paths.
1. Move associated images under `static/images/handbook/` to match the new handbook path
   and update all references. Check shared usage before moving a directory; preserve page-bundle resources.
1. Run all applicable repository linter scripts against the complete MR diff, including
   committed changes. Check rendered destination pages, images, and old-URL redirects.
   If local checks cannot run, wait for the latest CI/CD results, inspect failures, and
   fix them before reporting completion. Report missing coverage explicitly.
1. After the move merges, give the user a list of open merge requests that still change
   the old paths, marking those that add files there as potential breaking changes.
   Don't contact their authors; the user decides whether to notify them.

See the skill for redirect retention exceptions, validation commands, and recovery guidance.

## Toolchain, build, and preview

Use the versions pinned in `.tool-versions`. Hugo Extended is required for Sass processing.

If `mise` or another required pinned tool is unavailable, do not install or substitute an arbitrary
version, extract dependencies from unrelated images or artifacts, or use other installation
workarounds. See [Validation](#validation) for Docker Compose and CI fallbacks.

Read the checkout's `Makefile` and synchronization script before running build commands:

```shell
mise install
npm ci
make view          # clean, sync data, and preview at http://localhost:1313
make build         # clean, sync data, and render to public/
make clean         # remove generated public/
```

Both `make view` and `make build` run `scripts/sync-data.sh` automatically; a separate sync is
unnecessary before either command. Synchronization needs network access and overwrites synchronized
files. Run it when current upstream data is needed, not for every content-only edit. Check the
script for its required tools rather than assuming identical dependencies across projects.

For local theme development, temporarily add a replacement in the consuming handbook's `go.mod`:

```go
replace gitlab.com/gitlab-com/content-sites/docsy-gitlab => /absolute/path/to/docsy-gitlab
```

For authenticated GitLab API data, use `HUGOxPARAMSxGITLAB_API_KEY` without exposing its value.

## Validation

### Choose the scope

- List changes with `git diff --name-only` and `git status --short`. Include staged changes and
  committed MR changes against the target branch.
- **Plain text:** lint and Vale the changed Markdown.
- **Front matter, links, shortcodes, includes, or assets:** lint and build or preview affected pages.
- **Shared behavior, configuration, dependencies, or scripts:** run a full build and relevant
  script checks. Test shared theme behavior and dependency upgrades locally and in both handbook review apps.
- **Generated data:** verify the generating command and its complete diff.
- Prefer explicit file paths or the supported target-branch comparison. `make lint` in a dirty
  worktree may include unrelated changes and miss committed MR changes.

### Run the checks

```shell
markdownlint-cli2 path/to/changed-file.md
vale --no-wrap --minAlertLevel error path/to/changed-file.md
```

- **Missing Markdownlint or Vale:** use `docker compose run --rm` with an existing lint service.
  If none exists, use a temporary Compose file with the images and versions pinned in `.gitlab-ci.yml`
  or its included configuration. Mount the checkout, use its working directory and lint rules,
  and pass explicit file paths with the CI job's relevant options. Prefer Compose over `docker run`.
- **Docker Compose unavailable or failing:** report the limitation and use the MR pipeline for validation.
- Do not use `latest` or extract tools from images.
- For CI-only failures, inspect `.gitlab-ci.yml` and `scripts/handbook-lint.sh`.

### Verify and report results

- Confirm the intended files were processed using file lists, counts, or structured results.
  **A zero exit status with zero files checked is not validation.**
- Investigate skipped files and ignore rules. Use a supported explicit-file invocation with the
  repository's rules, or report the files as skipped.
- Do not weaken checks, add blanket exclusions, or add front matter solely to make an agent guide pass.
- In the handoff, state changed files, checks run, integration coverage, and checks that could not run.

## CI/CD and metrics

- Use `extends` and `rules`; do not add YAML anchors, `only`, or `except`.
- Preserve logs, metrics, profiling, and report artifacts, including default-branch baselines.
  Remove observability only on explicit user request.
- Preserve project-specific CI settings in `.gitlab-ci.yml`. Keep shared scripts identical as described
  in [Shared files](#shared-files); record out-of-scope synchronization in the MR.
- Keep scripts small and documented. Test input validation and failure handling, preserve command
  failures, and verify metrics uploads and companion pipelines before claiming success.

## Shared files

Docsy GitLab is the source of truth for these files. Maintain one byte-for-byte copy of each in all
three projects:

- `AGENTS.md`, `CLAUDE.md`, and `.gitlab/duo/mr-review-instructions.yaml`
- `skills/handbook-path-rename/`
- `compose.yml` and `scripts/docker-entrypoint.sh`
- `scripts/ci-helper-metrics.sh`, `scripts/hugo-build-with-metrics.sh`, and `scripts/vale.sh`

Synchronize shared files in this order:

1. Compare each handbook copy with the Docsy version before changing it. If a handbook copy has
   changes that Docsy lacks, such as manual edits, move them into Docsy first. Never overwrite them.
1. Make the change in Docsy, then copy the complete file contents to the public and internal
   handbooks.
1. After committing, confirm the copies with matching `git rev-parse HEAD:<path>` output in all three
   projects. This works for files and skill folders.

`.agents/skills/handbook-path-rename` and `.claude/skills/handbook-path-rename` are symlinks to
`skills/handbook-path-rename/` in each project. Synchronize only the skill directory's files. Do not
replace, copy, or recreate the symlinks. After synchronization, both must still show mode `120000`:

```shell
git ls-tree HEAD .agents/skills/handbook-path-rename .claude/skills/handbook-path-rename
```

When you add a skill to Docsy, decide whether the handbooks need it. For a shared skill, add its
`skills/<name>/` folder to the list above in the same MR. Then copy the folder to both handbooks and
create its `.agents/skills/` and `.claude/skills/` symlinks there once. Docsy-only skills, such as
`handbook-theme-release`, stay off the list. `skills/README.md` is maintained per project.

- Express repository-specific requirements in the shared files. Keep shared scripts and configuration
  project-agnostic: use predefined CI/CD variables instead of project IDs, paths, or names.
- Keep `CLAUDE.md` as a pointer containing only `@AGENTS.md`. Each repository needs its own copy of
  the Duo review file; these instructions do not configure automatic inheritance.
- Include synchronization in companion MRs, or record the follow-up when it is outside the task's
  scope. Preserve SAFE requirements and existing CODEOWNERS approval groups.

## Project maintenance files

Maintain `.gitlab/CODEOWNERS`, `.gitlab-ci.yml`, and `README.md` for the local project. Preserve its
license, ownership, and development environment. When architecture, tooling, or CI behavior changes,
update the relevant shared agent and review instructions in Docsy.

## Merge request preparation

1. Work in the relevant checkout on a dedicated branch. Continue an existing task's MR when present.
1. Check the final diff against `.gitlab/duo/mr-review-instructions.yaml` before committing or
   updating the MR.
1. Read the matching description template listed below. Describe the final change and validation,
   preserve applicable quick actions and checklist content, and apply labels through the GitLab tool.
1. Call out maintainer-file deletions under `.gitlab/`, `config/`, `assets/`, `layouts/`, or root
   configuration as potentially breaking. Request review from `@gitlab-com/content-sites/handbook-tools`
   as directed by the review instructions and the user's authorized review scope.
1. After creating or pushing to the MR, check the latest pipeline and Duo or human review feedback.
   Report whether CI passed, failed, or is running, and summarize unresolved review threads.
1. Fix small, low-risk review findings within scope in the same MR. Ask the user when feedback
   requires a decision or broader changes. Resolve threads only after verifying the fix is present.

## Repository-specific instruction paths

### Docsy GitLab

This project provides shared layouts, partials, shortcodes, assets, and development documentation.

- `layouts/_partials/`, `layouts/_shortcodes/`, and `layouts/_markup/` contain shared rendering logic.
- `assets/scss/` and `assets/js/` contain theme styles and JavaScript; `static/` is copied to the site.
- `content/docs/` is the canonical development and editing documentation.
- `content/handbook/` contains example or fixture content for theme behavior.

Inspect callers and both handbook integrations before changing shared behavior. Preserve Hugo context
contracts, CSS classes, rendered markup, and shortcode interfaces unless a breaking change is requested.
Keep partials focused, use explicit `dict` contexts where established, and reuse existing Sass and
JavaScript conventions. JavaScript must tolerate pages without optional elements. Add representative
fixtures and document new shortcode parameters under `content/docs/`.

Keep handbook-specific behavior in the relevant handbook. Follow the existing release automation
and `content/docs/development/`; roll out to the internal handbook before the public handbook.

- Content template: `.gitlab/merge_request_templates/Content-change.md`.
- Operations template: `.gitlab/merge_request_templates/Default.md`.
- Development entry point: `content/docs/development/_index.md`.

### Public handbook

This project contains public Markdown content and site-specific configuration for
[handbook.gitlab.com](https://handbook.gitlab.com/).

- `content/handbook/` contains most handbook pages.
- `content/job-description-library/` contains another top-level section.
- Use site-root links such as `/handbook/.../` or valid relative Markdown links for public pages.
- Implement shared rendering behavior in Docsy; keep only intentional public-handbook overrides here.
- Docker preview and build targets are `make docker-view` and `make docker-build`. For memory-limited
  Hugo server previews, consider `--renderToDisk`; do not assume this is a Hugo build flag.

Read the [SAFE framework](https://handbook.gitlab.com/handbook/legal/safe-framework/) before moving
information from internal sources into this public project. Do not copy internal content without
explicit authorization.

- Content template: `.gitlab/merge_request_templates/Default.md`.
- Operations template: `.gitlab/merge_request_templates/Handbook-Operations.md`.
- Development documentation: <https://handbook.gitlab.com/docs/development/>.

### Internal handbook and SAFE

This project contains internal Markdown content and site-specific configuration. Most pages live
under `content/handbook/`; shared rendering and development documentation come from Docsy.

Keep internal information in approved internal systems. Before adding or moving content, confirm it
belongs in the internal rather than public handbook under the
[SAFE framework](https://handbook.gitlab.com/handbook/legal/safe-framework/). Never copy internal
content into the public handbook or external services without explicit authorization. This includes
content quoted in public issues, MR descriptions, test fixtures, and diagnostic artifacts.

Use relative Markdown or site-root links for internal-handbook pages. Implement shared rendering behavior in Docsy;
keep only intentional internal-handbook overrides here. Review internal integration results without
publishing internal content in public companion MRs.

- Content template: `.gitlab/merge_request_templates/Default.md`.
- Operations template: `.gitlab/merge_request_templates/Handbook-Operations.md`.
- Development documentation: <https://internal.gitlab.com/docs/development/>.
