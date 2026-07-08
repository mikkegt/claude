---
description: Sweep ALL open PRs of a repo to done — CI, bot comments, fixes, merge — one by one. Use when the user says "openなPRを順次マージ", "全部のPRをみて", "CI監視してマージし、終わったら続きを", "PRぜんぶ片付けて". For a single PR's bot-review loop use gh-review-loop; for post-merge cleanup use pr-merge-tidy.
---

# PR Babysit

Iterate over every open PR in the repo until the queue is empty.

## Steps

1. **Queue**: `gh pr list --state open --json number,title,mergeable,reviewDecision,statusCheckRollup`
   Order by readiness: green CI + approved + no conflicts first; drafts last.
2. **Per PR**:
   - `gh pr checks <n>` — red? apply the ci-fix skill flow on that branch
   - Read ALL bot reviewers' comments (CodeRabbit, Sourcery, Codex) —
     triage per global PR Bot Review Handling rules; fix or reply
   - Conflicts? merge the base branch INTO the PR branch (never rebase)
   - Green + triaged → confirm with the user, then `gh pr merge <n> --merge`
     (never squash). Close linked issues that the merge resolves.
3. **After each merge**: `git checkout <default> && git pull`, then update
   remaining PR branches that now conflict (merge default in, never rebase).
4. **Loop** to the next PR until the queue is empty.
5. **Report**: end with a table — PR | action taken | merged/blocked/skipped | why.

## Rules

- One PR at a time; never batch-merge without per-PR confirmation.
- A PR that needs human product judgment (design questions, unclear intent):
  mark "blocked — needs user", summarize the open question, move on.
- If asked to also release afterward ("マージ、publish release"), chain into
  the publish skill once the queue is done.
- Long CI waits: watch in the background (`gh pr checks <n> --watch`) and
  work on the next PR meanwhile; come back when it flips.
