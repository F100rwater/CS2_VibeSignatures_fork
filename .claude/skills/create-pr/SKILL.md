---
name: create-pr
description: |
  Create a GitHub pull request from either staged task changes or an already-committed current branch. Use when the
  user asks to create or open a PR, including when there are no staged changes but the clean current branch is not
  main and has commits ahead of origin/main. Staged changes use the full immutable candidate lifecycle before commit;
  an already-committed branch is pushed and opened directly without rewriting its commits.
---

# Create Pull Request

Create one pull request using exactly one delivery mode:

- `staged-delivery` - deliver the caller's staged changes through candidate preparation, validation, publication,
  commit, push, and PR creation. Treat the index at invocation time as the authorized change set. The only additional
  paths this mode may stage are formatter updates to those same paths and validated
  `gamesymbols/<GAMEVER>.yaml` / `gamedata/<GAMEVER>/` outputs.
- `committed-branch` - when the index is empty, deliver the existing commits on a clean non-`main` current branch
  that is ahead of `origin/main`. Treat the captured `origin/main...HEAD` diff as the authorized change set. Do not
  format, stage, generate another commit, or rewrite existing commits in this mode.

Never mix the two modes in one invocation.

## Inputs

- `gamever` - required only for `staged-delivery`. Use the caller-provided value; if omitted in that mode, read
  `CS2VIBE_GAMEVER` from `.env`.
- `branch` - optional `dev*` branch name for `staged-delivery`. If omitted while on `main`, derive a concise
  `dev-<topic>` name from the staged change. Ignore this input in `committed-branch`; use the current branch exactly.
- `commit_title` - optional Conventional Commit title for `staged-delivery`. If omitted, derive it from the staged
  diff.
- `pr_title` / `pr_body` - optional PR text. If omitted, derive it from the delivered staged or committed diff and
  actual validation results.
- `issue` - optional GitHub issue number. Add `Closes #<issue>` to the PR body when supplied.

After selecting `staged-delivery`, resolve exactly one non-empty `GAMEVER`. Set
`ANALYSIS_CONFIG="configs/$GAMEVER.yaml"` and stop if that file does not exist. Never fall back to another game
version. `committed-branch` does not run the candidate lifecycle, so do not require or resolve a game version in that
mode.

## Safety Rules

- Run from the repository root and require an `origin` remote plus successful `gh auth status`.
- Never commit directly to `main`, force-push, amend an existing commit, or use `git add -A` / `git add .`.
- Preserve unrelated untracked files and never stage them.
- Require zero unstaged tracked changes at invocation. This forbids partially staged paths and prevents the
  formatter from absorbing unrelated work.
- In `staged-delivery`, treat the initial staged path list as immutable authorization. Do not add other source,
  config, reference, test, or documentation paths after the gates run.
- In `committed-branch`, require an empty index, a non-`main` attached branch, at least one commit ahead of
  `origin/main`, and a non-empty `origin/main...HEAD` diff. Keep `HEAD`, the current branch, and the committed path
  list unchanged until push.
- Stop on the first failed/non-runnable gate. Do not repair or retry inside this skill, and do not commit, push, or
  create a PR after a gate failure.

## Step 1: Select and Guard the Delivery Mode

Record the current branch and complete status, then inspect the index:

```bash
git branch --show-current
git status --short
git diff --cached --quiet
git diff --cached --name-only
git diff --cached --name-status
git diff --cached --stat
git diff --name-only
git ls-files --others --exclude-standard
git remote
gh auth status
git fetch origin main --prune
git rev-parse HEAD
git rev-parse origin/main
git rev-list --count origin/main..HEAD
git diff --name-only origin/main...HEAD
git diff --name-status origin/main...HEAD
git diff --stat origin/main...HEAD
```

`git diff --name-only` must be empty in both modes. If any unstaged tracked change exists, stop before formatting,
candidate creation, push, or PR creation and report the paths. Untracked files may remain, but record them and never
stage them.

Interpret `git diff --cached --quiet` as follows:

### Mode A - `staged-delivery`

Exit `1` proves staged changes exist. Save the exact `git diff --cached --name-only` result as
`INITIAL_STAGED_PATHS`, including staged additions, renames, and deletions. Read `git diff --cached` to understand the
change, detect accidentally staged unrelated files or credentials, and derive the commit/PR summary.

Validate the intended branch before running expensive gates:

- On `main`, choose the caller-provided `branch` or derive a valid, unused `dev-<topic>` name. Validate it with
  `git check-ref-format --branch <dev-branch>` and require that it does not exist locally or on `origin`.
- On an existing `dev*` branch whose `HEAD` still equals `origin/main`, use that branch unless the caller explicitly
  supplied the same name.
- On any other branch, stop and ask the caller to use `main` or a `dev*` branch.

### Mode B - `committed-branch`

Exit `0` means the index is empty. Allow this mode only when all of the following hold after fetching `origin/main`:

- `git branch --show-current` returns a non-empty branch name other than `main`;
- `git check-ref-format --branch <current-branch>` succeeds;
- `git rev-list --count origin/main..HEAD` is greater than zero;
- `git diff --quiet origin/main...HEAD` exits `1`, proving the PR would contain a non-empty committed diff.

Otherwise stop with a specific error. Use these forms for the two common empty-index failures:

```text
<skill_error>create-pr cannot run: no staged changes and the current branch is main or detached.</skill_error>
<skill_error>create-pr cannot run: no staged changes and the current branch has no committed changes ahead of origin/main.</skill_error>
```

Capture `INITIAL_BRANCH`, `INITIAL_HEAD`, `AHEAD_COUNT`, and the exact `git diff --name-only origin/main...HEAD` result
as `INITIAL_COMMITTED_PATHS`. Read `git diff origin/main...HEAD` and `git log --format=fuller origin/main..HEAD` to
understand the complete PR change, detect unrelated files or credentials, and derive the PR title/body. Ignore the
optional `branch` input and use `INITIAL_BRANCH` as the PR head.

Any exit code from `git diff --cached --quiet` other than `0` or `1` is a hard stop.

For either mode, set `PR_BRANCH` to the intended dev branch or captured current branch. Check
`gh pr list --state open --head <PR_BRANCH> --json url`. Stop if an open PR already exists for it. Never create a
duplicate PR.

## Step 2: Prepare the Immutable Candidate

Run Steps 2 through 6 only in `staged-delivery`. In `committed-branch`, skip directly to Step 7 without running a
formatter, candidate command, publication command, staging command, or commit command.

In `staged-delivery`, **ALWAYS** Use SKILL `/prepare-post-change-candidate` with the resolved `gamever`.

Retain the returned candidate path, candidate session path, gamedata session path, and candidate SHA-256. If the
skill fails, stop the entire task.

After preparation, inspect `git diff --name-only`. Formatting may have changed a path only when it belongs to
`INITIAL_STAGED_PATHS`. If any other tracked path changed, stop and report it; do not stage it or continue.

## Step 3: Validate the Exact Candidate

In `staged-delivery`, **ALWAYS** Use SKILL `/post-change-validation` with the same `gamever`, candidate path, and
candidate session path returned by `/prepare-post-change-candidate`.

Require explicit success, runnable C++ tests, and zero failure counters. If validation fails or is non-runnable,
stop exactly as that skill requires. Do not publish, commit, push, or create a PR.

## Step 4: Publish the Validated Candidate

Only after validation succeeds in `staged-delivery`, **ALWAYS** Use SKILL `/publish-post-change-candidate` with the
same `gamever`, candidate path, candidate session path, and gamedata session path.

Require the published snapshot SHA-256 to equal the validated candidate SHA-256. Publication may modify only:

- existing paths in `INITIAL_STAGED_PATHS` that were reformatted;
- `gamesymbols/$GAMEVER.yaml`;
- files under `gamedata/$GAMEVER/`.

Compare `git status --short` with the status recorded in Step 1. Any new or modified path outside that allowlist is
a hard stop. Preserve pre-existing unrelated untracked files and leave them untracked.

## Step 5: Refresh the Authorized Index

Refresh formatter changes only for existing files in `INITIAL_STAGED_PATHS`, passing every path explicitly:

```bash
git add -- <explicit-existing-initial-staged-paths>
git add -- "gamesymbols/$GAMEVER.yaml" "gamedata/$GAMEVER"
```

Already-staged deletions need no refresh. Never use a repository-wide add command.

Then verify:

```bash
git diff --name-only
git diff --cached --quiet
git diff --cached --name-only
git diff --cached --stat
```

Require zero unstaged tracked changes and a non-empty staged diff. Every final staged path must be either an initial
staged path or an allowed current-version publication path. Review the final cached diff before committing.

## Step 6: Create the Commit on a Dev Branch

If currently on `main`, create the validated branch now:

```bash
git switch -c <dev-branch>
```

If already on the intended `dev*` branch, remain there. Derive or validate `commit_title` using the repository
format `<type>(scope): <summary>`: start with a verb, keep it at most 100 characters, and omit the final period.

Commit exactly the staged index:

```bash
git commit -m "<commit_title>" -m "Co-Authored-By: Codex"
```

Verify the new commit's changed paths match the final staged path list and that no unstaged tracked changes remain.
Do not amend if the verification fails; stop and report the mismatch.

## Step 7: Push and Create the Pull Request

In `committed-branch`, re-run the following immediately before push:

```bash
git branch --show-current
git rev-parse HEAD
git diff --cached --quiet
git diff --quiet
git rev-list --count origin/main..HEAD
git diff --name-only origin/main...HEAD
```

Require the branch to equal `INITIAL_BRANCH`, `HEAD` to equal `INITIAL_HEAD`, both index and tracked worktree to be
clean, the ahead count to remain greater than zero, and the committed path list to equal `INITIAL_COMMITTED_PATHS`.
Stop if any captured state changed. This mode must not create a new commit.

Push without force:

```bash
git push -u origin <PR_BRANCH>
```

Build the PR title from `pr_title` when supplied. Otherwise, use the new commit title in `staged-delivery`; in
`committed-branch`, derive a concise title from `git log --format=%s origin/main..HEAD` and the committed diff.

Build the body from the delivered committed diff and actual results. Never claim a validation that this invocation
did not run. Use this concise shape for `staged-delivery`:

```markdown
## Summary
- <behavioral change>
- <supporting change>

## Validation
- implementation-specific tests: <commands/results supplied by the caller>
- candidate preparation: passed for `<GAMEVER>`
- C++ post-change validation: passed with runnable tests and zero failures
- candidate publication: passed; published SHA-256 matches the validated candidate

Closes #<issue>
```

For `committed-branch`, replace the candidate lifecycle lines with truthful evidence for the existing commits:

```markdown
## Validation
- implementation-specific tests: <commands/results supplied by the caller, or "not supplied">
- existing committed branch: `<AHEAD_COUNT>` commit(s) ahead of `origin/main`; clean index and tracked worktree
```

Omit the issue line when no issue was supplied. Create the PR explicitly against `main`:

```bash
gh pr create --base main --head <PR_BRANCH> --title "<pr_title>" --body "<pr_body>"
```

Report the branch, commit SHA, pushed remote, PR URL, game version, candidate SHA-256, and the final committed path
list for `staged-delivery`. For `committed-branch`, report the branch, HEAD SHA, ahead count, pushed remote, PR URL,
and `INITIAL_COMMITTED_PATHS`; omit game-version and candidate claims. If push succeeds but PR creation fails, report
the remote branch and exact failure; do not delete the branch, force-push, or create another commit.

## Checklist

- [ ] Exactly one mode was selected: non-empty initial index, or clean non-`main` branch ahead of `origin/main`.
- [ ] No unstaged tracked changes existed at invocation.
- [ ] `staged-delivery`: initial cached diff is task-related; all candidate gates passed; final staged paths are
      authorized; commit is on a `dev*` branch and follows repository format.
- [ ] `committed-branch`: index/worktree are clean; branch, HEAD, ahead count, and committed paths remain unchanged;
      no formatter, candidate publication, staging, or commit command ran.
- [ ] No duplicate open PR existed; branch was pushed without force; exactly one PR was created against `main`.
