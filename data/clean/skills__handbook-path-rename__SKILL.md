# Rename handbook paths

Complete a handbook path change without leaving broken links, images, or navigation.
Work in the affected handbook checkout and follow its `AGENTS.md` and review instructions.
Docsy maintains this skill; it does not contain the production handbook pages to move.

## Sources and scope

The [development guide source](https://gitlab.com/gitlab-com/content-sites/docsy-gitlab/-/raw/main/content/docs/development/_index.md)
defines redirect retention. The [contributor guide source](https://gitlab.com/gitlab-com/content-sites/handbook/-/raw/main/content/handbook/about/editing-handbook/_index.md)
describes moving pages and placing images. Essential requirements are included below
so ordinary moves do not require additional lookups.

Establish the old and new source paths and rendered URLs before editing. Inspect
front matter such as `url` and `slug`, section `_index.md` files, and page bundles;
a filesystem rename alone does not prove that the URL changed. For a new single page,
follow the layout of its new siblings, for example `<section>/<page>.md` next to other
single-file pages. Moving a page to another section also moves it in the sidebar.

## Requirements

- A branch of the affected handbook from the latest `origin/main`, in a checkout or worktree
  under your home directory. Planning can read a recently fetched `origin/main`; create the
  branch before the first edit. Docker can only mount shared paths, so a copy in a temporary
  directory looks empty to containers.
- The tools pinned in that branch's `.tool-versions`. Where a pinned tool is missing, use
  Docker Compose or the CI image of the same version instead. See the checkout's `AGENTS.md`.
- For CI validation: the [GitLab CLI (`glab`)](https://docs.gitlab.com/cli/), checked with
  `glab version` and `glab auth status`, or the
  [GitLab MCP server](https://docs.gitlab.com/user/model_context_protocol/mcp_server/),
  checked with its `get_mcp_server_version()` tool.

If neither the local tools, Docker, nor the MR pipeline can run the checks, stop and ask
the user to fix it.

## Authorization boundaries

- A rename request authorizes the file moves, reference updates, and redirects in the
  affected handbook.
- It does not authorize publishing internal content, merging, or contacting reviewers.
  Keep public and internal content in their authorized repositories.
- Follow the user's requested review boundary before publication or synchronization to
  another repository.

## Move content and repair references

1. Inventory the affected pages and resources, then move tracked files with `git mv`.
   Preserve content, controlled-document metadata, and meaningful heading anchors.
1. Search the whole repository for the old source path, site-root URL, full URL,
   image prefix, and the bare file name, which relative links such as `<page>.md` use.
   Use `rg -n -F -- '<pattern>' .` for each and inspect hidden locations such as
   `.gitlab/` explicitly. Search variants with and without trailing slashes.
1. Search the other handbook, `gitlab-com/content-sites/docsy-gitlab`, and
   `gitlab-com/www-gitlab-com` for the URL and the source path, then run a group-wide blob
   search in `gitlab-com` as a final check. Prefer `git grep` in up-to-date local clones; an empty
   `glab api "projects/<id>/search?scope=blobs&search=<pattern>"` result can also mean the
   project isn't indexed. Redirects cover rendered URLs, but not raw file links such as
   `.../-/raw/main/content/...`. Report references outside the affected handbook as
   follow-ups instead of changing them.
1. Update landing pages, `data/toc.yaml` where present, relative Markdown links,
   shortcodes, includes, scripts, automated MR comments, and CODEOWNERS patterns.
   Check links from moved pages as well as links to them; changing directory depth can
   break relative links that do not contain the old path. Keep the link style of the
   surrounding text: a relative link stays relative, for example `../<page>.md`.
1. Preserve existing owners. If a page leaves a directory pattern in `.gitlab/CODEOWNERS`,
   add an explicit rule for the new path in the same section with the same owners.
1. Inventory the images from the moved pages' image references, not from a folder name:
   images often live in the section's folder rather than in
   `static/images/handbook/<old-path>/`. Move images used only by the moved pages to the
   folder for the new path, for example `static/images/handbook/<new-section>/<page>/`,
   and update Markdown, HTML, shortcode, and configuration references. Check shared usage
   first, including other repositories that embed the image URLs: do not move unrelated
   images with a whole directory or delete an image still used elsewhere. Keep resources
   already in page bundles with their pages.

## Add redirects

Use `layouts/index.redirects` in the affected handbook. Do not add Hugo front matter
`aliases`. Preserve existing aliases unless migrating them is part of the task.

Group entries by the move under `# <description> - remove YYYY-MM-DD` and insert the
group in chronological removal-date order. Existing groups are not always sorted; place
the new group between the nearest earlier and later removal dates. For a move within
one handbook, retain redirects for three calendar months from the change date,
clamping to the last day of the destination month when needed. Cross-handbook
redirects use 3–6 months; external destinations use 3–12 months. Establish the
appropriate date within those ranges with the content owner. Preserve designated
permanent legal/compliance redirects.

For example, a move on September 24, 2026 uses:

```text
# Move example page to the new section - remove 2026-12-24
/handbook/old-section/example/ /handbook/new-section/example/ 301
```

Use exact entries for individual pages and partial directory moves. A subtree
wildcard is appropriate only when the entire subtree moves with matching suffixes;
check the section root separately. Inspect existing redirects for conflicting rules,
loops, and chains; point affected old rules directly at the final destination.

HTTP redirects cannot match URL fragments. Preserve important old heading anchors
at a useful destination and update incoming fragment links when headings change.

## Validate

1. Review `git diff --name-status <target>...HEAD`, staged changes, and unstaged changes.
   Confirm every intended move and reference update, including the image inventory.
   Search again for old paths and explain intentional matches such as redirect sources.
1. Read the checkout's current `.gitlab-ci.yml`, `Makefile`, and linter scripts.
   Run all applicable checks: Markdownlint, Vale, `scripts/handbook-lint.sh`, Hugo link
   checks, and any project-specific scripts required by CI. Use their supported file
   or branch arguments; do not assume identical interfaces across the handbooks.
   Scripts that compare against a local `main` give wrong results when it is behind
   `origin/main`; compare against `origin/main` or update `main` first.
   Include committed MR changes and verify that checks actually processed the files.
1. Build or preview the affected pages and inspect navigation, heading links, and
   images. Check rendered redirect output and test old URLs in an environment that
   applies GitLab Pages redirects; a Hugo server alone does not validate them.
1. If local tools are unavailable, use the authorized MR pipeline. Wait for the latest
   commit's CI/CD results, inspect job logs and reports, and fix relevant failures.
   Repeat affected checks after fixes. A running pipeline or zero files checked is
   not successful validation. Report checks CI does not cover, including rendered
   behavior that could not be exercised.

In the MR, record old and new URLs, redirect removal dates, navigation and image
changes, validation results, and any missing coverage.

## Report open merge requests that target the old paths

After the move merges, other open merge requests may still change files under the old
paths. Identify them and report the list. A rename does not authorize commenting on
other contributors' merge requests.

Use whichever access the environment provides:

- GitLab MCP server tools, to list open merge requests and read their changed paths.
- `glab` CLI: list the open merge requests, then read each one's changed paths from
  `glab api "projects/<id>/merge_requests/<iid>/diffs"`, which diffs against the merge
  request's own target branch. Combine paginated results with `jq -s add`.
- Local Git, which stays reliable in a repository with many merge requests:

  ```shell
  git fetch origin '+refs/merge-requests/*/head:refs/remotes/mr/*'
  git diff --name-only origin/main...refs/remotes/mr/<iid>
  ```

Check both `gitlab-com/content-sites/handbook` and
`gitlab-com/content-sites/internal-handbook`, and cover every renamed prefix, including
`static/images/`, `static/images/handbook/` and `static/pdfs/`. Check both the old and the
new path of each change.

Report each affected merge request, and whether it adds, modifies, or deletes files
at the old path. A rename into an old prefix counts as an add. Two cases need care:

- Merge requests that **add** files rebase cleanly and recreate the old section
  alongside the new one. No linter or link check detects this, so report them
  separately as potential breaking changes.
- With local Git, intersect the results with the open merge request list, because merge
  request refs also include merged and closed ones. A merge request whose target is not
  the default branch is stacked on another branch: diff it against its actual target.
  Diffing against the default branch also returns its parent's changes and misstates
  what the merge request does. The API and MCP diffs already use the actual target.

Hand the list to the maintainer, who decides whether to notify the authors and ask
them to rebase and resolve conflicts.

## If something fails

- **The move was interrupted:** inspect the current diff and continue from the existing
  old-to-new mapping. Preserve unrelated edits; do not rerun broad replacements or
  reset the checkout.
- **Validation is blocked by access or infrastructure:** identify the blocker and leave
  validation pending rather than claiming completion.
