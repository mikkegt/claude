---
description: After a PR merges, sweep up the trailing chores — comment on the linked issue with a final summary, decide whether to close it or just leave a progress note, and move any plan file the PR introduced from `plans/` to `plans/done/`. Reduces the "merged the PR but the issue is still open and the plan still says 'pending'" backlog.
---

# PR Merge Tidy — close the loop after a merge

## When to use

A PR just merged. Linked issue is still open. The plan file the
PR was tracking against (e.g. `plans/feat-ask-user-choice.md`) is
still in `plans/`, not `plans/done/`. This skill tidies all three
in one shot.

Skip when:

- The PR isn't merged (`gh pr view <N> --json state` ≠ `MERGED`).
- The PR was a hotfix with no linked issue or plan file.
- The user already manually tidied — check before opening a chore
  PR for the plan move so we don't duplicate work.

## Inputs

PR URL or number. If only `<N>`, infer owner/repo from
`gh repo view --json nameWithOwner`.

### Default: no argument → infer from current directory

If invoked with no PR number / URL, derive the PR from the
current git context. Common case: the user just ran
`gh pr merge` and stayed in the working tree of the merged
branch — the skill should auto-target that PR.

```bash
OWNER_REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Prefer the merged PR whose head is THIS branch — that's the PR
# the user just merged from this working tree. The last merge
# commit on the branch can belong to someone else's PR (e.g. a
# main-sync merge or another PR that landed after ours).
HEAD_PR=$(gh pr list --repo "$OWNER_REPO" --head "$BRANCH" --state merged \
          --limit 1 --json number --jq '.[0].number')

# Fallback: back on `main` after a `--delete-branch` merge, the
# head lookup misses — use the last merge commit's PR number.
LAST_MERGE_PR=$(git log -1 --merges --pretty=%s | grep -oE '#[0-9]+' | head -1 | tr -d '#')

PR_N="${HEAD_PR:-$LAST_MERGE_PR}"

if [ -z "$PR_N" ]; then
  echo "No PR found for branch '$BRANCH' in $OWNER_REPO." >&2
  echo "Run with an explicit PR number, e.g. /pr-merge-tidy 805" >&2
  exit 1
fi
```

Surface the inferred PR number to the user before proceeding so
they can abort if the inference picked the wrong PR (e.g. the
last merge on this branch was a stale merge from days ago).

## Wait-for-CI mode (pre-merge)

When the user says 「ci通ったらマージ」 ("merge once CI is green") or
similar, the PR isn't merged yet — run this mode first:

1. `gh pr checks <N> --watch` in the background; report failures as
   they appear and fix them (use `gh-review-loop` for the fix-push
   loop when bots are involved).
2. Once all checks are green, triage any new bot comments.
3. Confirm with the user, then `gh pr merge <N> --merge`.
4. Continue with the tidy steps below.

「マージ手前まで」 ("stop at merge-ready"): do steps 1-2 only, report
merge-ready, and stop without merging.

## Steps

### 1. Confirm MERGED

```bash
gh pr view <N> --json state,mergeCommit,body,title,url
```

Stop if state ≠ MERGED. Capture the merge commit SHA and PR body.

### 2. Find linked issues

Parse the PR body for these patterns (case-insensitive, allow
GitHub's keyword set):

- `Closes #<num>` / `closes #<num>` / `close #<num>`
- `Fixes #<num>` / `fixes #<num>` / `fix #<num>`
- `Resolves #<num>` / `resolves #<num>` / `resolve #<num>`
- `Refs #<num>` (no auto-close — just a reference)
- Plain `#<num>` mentions in the body (loose link)

The first three keyword groups auto-closed on merge. The `Refs`
group did not. Capture both lists.

### 3. For each auto-close-keyword issue

GitHub already flipped them to closed at merge time. Add a final
summary comment so the close is informative, not silent:

```bash
gh issue comment <issueN> --repo <owner>/<repo> --body "$(<final-summary>)"
```

Body shape:

```markdown
## Closed via #<PR-N> — merge commit `<sha>`

<one paragraph describing the change in a sentence>

### What landed
- <bullet>
- <bullet>

### Out of scope (separately tracked or deferred)
- <bullet — only if the issue mentioned multiple sub-items and only some shipped>
```

If the issue had multiple sub-items and the PR only addressed
some, list the remaining ones explicitly under "Out of scope" so
a reader doesn't think everything was solved.

### 4. For each `Refs` issue

These stay open. Add a progress comment with what shipped, what's
next:

```bash
gh issue comment <issueN> --repo <owner>/<repo> --body "$(<progress-comment>)"
```

Body shape:

```markdown
## Progress (PR #<PR-N> merged at `<sha>`)

### Done in this PR
- <bullet>

### Still open
- <bullet>
- <bullet>
```

Do NOT close `Refs` issues — those were intentionally referenced
without closing intent. If the issue's open scope LOOKS empty
after this merge (every sub-item now done), surface that in the
chat output and ask the user if they want to close it manually.

### 5. Detect plan file moves

Read the PR diff:

```bash
gh pr diff <N> --patch | grep -E "^\+\+\+ b/plans/" | grep -v "^\+\+\+ b/plans/done/"
```

For each new file under `plans/` (not `plans/done/`) that
**this PR introduced** (so was the original plan, not an audit
plan that's still being executed), mark it as a candidate to
move.

Caveat: PR1 of a multi-PR roadmap (e.g. `plans/audit-journal-subsystem.md`
introduced in #800, then PRs #801/#805/#810/#820 referenced it)
should NOT move until the LAST referenced PR merges. Heuristic:

- If the plan file's title says "audit" or "roadmap" or
  references multiple PRs, ask the user before moving.
- If the plan is single-feature single-PR (typical), move.

### 6. Move the plan file

Confirm with the user before pushing the chore branch and opening
the PR — pushes need explicit approval.

For each plan to move, create one chore PR:

```bash
git fetch origin main
git checkout main
git pull origin main
git checkout -b chore/move-plans-to-done-<PR-N>

git mv plans/<file>.md plans/done/<file>.md
git commit -m "chore: move plans/<file>.md to plans/done/ (PR #<PR-N> merged)"
git push -u origin chore/move-plans-to-done-<PR-N>
```

Open the PR:

```bash
gh pr create --base main --head chore/move-plans-to-done-<PR-N> \
  --title "chore: move <file>.md to plans/done/ (#<PR-N> merged)" \
  --body "Tidy follow-up to #<PR-N>. Plan file landed during the original PR, work is done, moving to plans/done/ per repo convention."
```

If multiple plan files move at once (e.g. you're tidying after
several PRs in a row), batch them in a single chore PR.

### 7. Report

To the user (chat), one short summary:

> ## Tidy report
>
> - Closed #<issue> with summary comment
> - Refs #<issue> updated with progress
> - Plan moved: `plans/<file>.md` → `plans/done/<file>.md` (chore PR #<chore-N>)
>
> Outstanding: <anything to manually decide, like "should I close #<X>? It looks done">

## Don'ts

- Don't close a `Refs`-keyword issue — that wasn't the PR's
  intent. Leave it for human judgment after seeing the progress
  comment.
- Don't move a plan file that other in-flight PRs reference
  (audit / umbrella plans). Check by `grep -r "plans/<file>.md"`
  in PR descriptions of currently-open PRs.
- Don't post duplicate comments. If a prior `pr-merge-tidy`
  comment already exists on the issue, replace it instead of
  stacking:
  `gh api --method PATCH repos/<owner>/<repo>/issues/comments/<comment-id> -f body="<new body>"`.
  Detect via the marker `<!-- pr-merge-tidy:auto-generated -->`
  in the body.
- Don't push the chore PR straight to main even if branch
  protections allow — keep the PR + review pattern consistent.

## Failure modes

- **PR isn't MERGED**: stop, report state.
- **No linked issues found in body**: still scan for plan files.
  Skip step 3-4. Some PRs are pure chores with no issue.
- **Plan file already moved (worktree dirty / move PR exists)**:
  detect existing move PR via `gh pr list --search "plans/<file>"`
  and report to user instead of creating a duplicate.
- **Issue is already closed**: still post the summary comment so
  a future reader sees the wrap-up. Don't try to re-close.

## Out of scope (v1)

- Auto-detecting which PRs in the recent merge log haven't been
  tidied (a sweep mode). Could be added later but for now this
  skill is one-PR-at-a-time.
- Updating `docs/CHANGELOG.md` — that's the release flow, not
  per-merge.
- Deleting the merged branch — most PR-merge tools already do
  this (`gh pr merge --delete-branch` if not default).
- Cross-repo issue updates (the issue lives in the same repo as
  the PR by assumption).
