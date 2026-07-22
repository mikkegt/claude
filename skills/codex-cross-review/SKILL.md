---
description: Dual-reviewer loop on a GitHub PR. User pastes a PR URL or number; you invoke Codex to review and post findings, then YOU critically evaluate each finding (necessity, side effects, missing related issues), apply valid fixes, re-request Codex, and repeat until both reviewers agree. Throughout the loop you monitor CI, sync main, and resolve conflicts. Merge only when both reviewers are OK and CI is green.
---

# Codex Cross-Review

Two-reviewer convergence loop. Codex raises findings; you (Claude Code) evaluate them with full context, apply real fixes, and request a follow-up review. Both reviewers must sign off before merge.

## Inputs

The user supplies a PR URL (`https://github.com/<owner>/<repo>/pull/<N>`) or just a number in the current repo context. Parse out `<owner>/<repo>` and `<N>`. If only a number, infer owner/repo from `gh repo view --json nameWithOwner`.

## Setup (once)

1. `date` — capture current ISO time so you can filter "new" comments per iteration.
2. `gh pr view <N> --json state,headRefName,baseRefName,mergeable,isDraft,statusCheckRollup` — confirm OPEN & not draft. If not, stop and report.
3. `gh pr checkout <N>` — check out the branch locally.
4. Resolve the default branch: `DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name)`. Then record `BASE_SHA = git merge-base "origin/$DEFAULT_BRANCH" HEAD` so you can detect new default-branch commits during the loop.
5. Read `CLAUDE.md` in the repo root (if present) for project-specific rules — they apply to every fix you commit.
6. Ensure `codex` CLI is installed (`command -v codex`). If missing, stop and tell the user to install `@openai/codex`.

## The Loop (max 5 iterations — safety cap)

Keep a per-iteration state file at `/tmp/codex-cross-review-<N>/iteration-<k>.json` summarising what Codex said, what you decided, and what you changed. Helps post-mortem if the loop spins.

### Iteration step A — request Codex review

Run Codex non-interactively with an explicit verdict contract:

```bash
codex exec --sandbox workspace-write \
  "Review PR #<N> at https://github.com/<owner>/<repo>/pull/<N>.

   Use the gh CLI to inspect the diff, then post inline review comments on specific lines via:
     gh api repos/<owner>/<repo>/pulls/<N>/comments
   or top-level comments via:
     gh pr comment <N>

   Focus on: correctness, edge cases, security (XSS / SSRF / path traversal / prompt injection),
   accessibility, i18n lockstep (if this repo has multi-locale dicts), tests coverage for the
   happy path + boundary cases, and consistency with the rest of the codebase.

   At the END of your work, ALWAYS post ONE final top-level comment that starts with a
   verdict marker on its own line:
     - 'CODEX VERDICT: LGTM' if you have no outstanding concerns
     - 'CODEX VERDICT: CHANGES REQUESTED' followed by a bulleted summary of remaining issues

   Do not apply any fixes yourself — only review and post findings."
```

Wait for `codex exec` to finish. If it errors out, record and stop the loop (ask user to rerun manually).

### Iteration step B — fetch what Codex posted *this iteration*

Filter by author and the timestamp captured at the start of the iteration:

```bash
gh api "repos/<owner>/<repo>/pulls/<N>/comments" --paginate \
  --jq "[.[] | select(.user.login | test(\"codex\"; \"i\")) | select(.created_at > \"$ITER_START\")]" \
  > /tmp/codex-cross-review-<N>/inline-<k>.json

gh api "repos/<owner>/<repo>/issues/<N>/comments" --paginate \
  --jq "[.[] | select(.user.login | test(\"codex\"; \"i\")) | select(.created_at > \"$ITER_START\")]" \
  > /tmp/codex-cross-review-<N>/top-<k>.json
```

Locate the verdict marker in the top-level comments. The line starting `CODEX VERDICT:` is the machine-readable signal.

### Iteration step C — YOU evaluate each finding

**This is not a passive apply step.** For every finding from Codex:

1. **Necessity** — Is this a real bug, a style preference, or a false positive? Reproduce the scenario mentally (or with a targeted grep / type-check) before accepting.
2. **Blast radius** — If Codex flags issue X at one site, search the codebase for the same pattern elsewhere. A single-site fix that leaves three other copies broken is worse than the original finding.
3. **Side effects** — Will the suggested fix break callers? Violate a convention? Regress a test? Check before applying.
4. **Gaps Codex missed** — Look at the diff yourself with fresh eyes. Codex's review is your starting point, not your ceiling.
5. **Categorise**: MUST-FIX / VALID-NIT / FALSE-POSITIVE / DEFER-TO-FOLLOWUP.

Apply MUST-FIX + VALID-NIT in this iteration. For FALSE-POSITIVE and DEFER cases, post a top-level reply explaining why you're not fixing them — Codex can then factor that into the next verdict.

### Iteration step D — local checks

After any code change, run the project's mandated checks (derived from CLAUDE.md or conventional defaults):

- `yarn format` (Prettier / similar)
- `yarn lint`
- `yarn typecheck`
- `yarn build`
- `yarn test` if unit tests exist
- Skip e2e in-loop by default (expensive, often env-dependent); CI will catch e2e regressions

If any check fails, fix and retry before pushing. Do **not** commit a red build into the loop — it breaks the shared state between reviewers.

### Iteration step E — sync the default branch (before every push)

```bash
git fetch origin "$DEFAULT_BRANCH"
NEW_MAIN=$(git rev-parse "origin/$DEFAULT_BRANCH")
if [ "$NEW_MAIN" != "$LAST_KNOWN_MAIN" ]; then
  git merge "origin/$DEFAULT_BRANCH" --no-edit
  # Resolve conflicts: if they're in files you edited this iteration,
  # prefer your edits but re-apply the main-side logic. If they're purely
  # structural (e.g., both sides added an import), auto-resolve.
  # If the conflict is semantic and unclear, pause and ask the user.
  LAST_KNOWN_MAIN=$NEW_MAIN
  # Re-run local checks after the merge — main may have changed contracts.
fi
```

### Iteration step F — commit + push

- `git add` only the files you touched intentionally. Never `git add -A`.
- Commit message: `fix: address codex review <iteration-<k>>` with a body listing the findings you accepted, in order. Include the current model's standard `Co-Authored-By` trailer.
- `git push` — normal, no force.

### Iteration step G — decide whether to loop

Parse the Codex verdict marker from step B:

- `CODEX VERDICT: LGTM` and your own evaluation has no remaining concerns → exit the loop, proceed to CI wait.
- `CODEX VERDICT: LGTM` but you found real issues Codex missed → fix them anyway, push, and go to the next iteration (Codex will re-verify your new commit).
- `CODEX VERDICT: CHANGES REQUESTED` → go to next iteration.
- No verdict marker found → treat as `CHANGES REQUESTED`, note the protocol failure, retry Codex with a reminder.

Stop at iteration 5 regardless and surface the stalemate to the user. Infinite review loops mean the two reviewers can't converge — that's a human-judgement call.

## CI monitoring (continuous, parallel to the loop)

Between every iteration — and continuously while waiting for CI after the loop ends — run:

```bash
gh pr checks <N> --json name,state,conclusion,link
```

**Handling CI failures:**

1. Identify the failing job.
2. Fetch logs: `gh run view <run-id> --log-failed`.
3. Reproduce locally if possible; otherwise read the log carefully.
4. Fix, run local checks, commit (use commit message `fix: CI <job-name> <short-reason>`), push.
5. Sync main first (step E).

**Handling merge conflicts from new main commits:** same as step E; this isn't rare — mainline typically moves during a review cycle.

Do not ignore a failing CI just because it looks unrelated to your changes — a pre-existing failure that you happen to be merging into IS your problem now. Escalate to the user only if the failure is clearly outside your scope (e.g., infrastructure / secrets).

## Merge (once both reviewers are OK AND CI is green)

1. Confirm with the user: "Codex LGTM + my evaluation clear + all CI checks green. Ready to merge?"
2. On user confirmation: `gh pr merge <N> --merge` (merge commit per project convention; NEVER squash unless the user overrides).
3. After merge: delete the local branch, confirm the mergeCommit SHA, and report the final state.

## Safety rules (always)

- Never skip local checks. Never `--no-verify` / `--no-gpg-sign` / `--force`.
- Never apply a Codex suggestion blindly. Every fix must pass your own review.
- If you disagree with Codex, SAY SO in a reply comment with reasoning — silent disagreement breaks the convergence protocol.
- Always sync main before pushing. Stale branches create artificial conflicts and confuse both reviewers.
- Never commit secrets. Never include `.env` or credential files in the diff.
- If you find issues Codex missed, do NOT pretend they came from Codex. Attribute them honestly in your commit message ("observed during Claude review, not flagged by Codex").
- Respect project-specific rules in `CLAUDE.md` — they override these defaults on conflict.

## What "OK" means from Claude's side

Not "Codex had nothing to say." Claude's own OK requires:

- No MUST-FIX findings remaining (either from Codex or your own reading).
- No obvious related issues in adjacent code that the diff invites but doesn't fix (if you deliberately deferred any, you posted a comment saying so with a rationale).
- All project checks pass locally.
- Test coverage matches the change shape — new logic has at least one test asserting the new behaviour.
- i18n / a11y / security conventions from `CLAUDE.md` are honoured.

Only then do you wait on CI and ask the user for the merge go-ahead.

## Reporting to the user

After every iteration, give the user a 3-4 line status:

- Iteration `<k>` of 5
- Codex verdict: `LGTM` / `CHANGES REQUESTED (<N> issues)`
- What you changed this iteration (1-line summary)
- CI status at this moment

Final report on merge: PR number, merge commit SHA, total iterations, notable disagreements if any.
