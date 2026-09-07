---
description: GitHub PR review-driven loop. Read whatever the GitHub-side bots (Codex via GitHub Actions, CodeRabbit, Sourcery) posted on the latest commit, evaluate each finding, apply real fixes, push, wait for the bots to re-review the new commit, repeat. There is no iteration cap — the loop runs until two consecutive clean rounds on an unchanged head, and stops early only for a decision that is genuinely the user's. A ledger comment on the PR keeps settled findings from being re-flagged, and every fifth round the whole PR is re-read to check the discussion is still aimed at the right thing. The loop can also conclude the PR should be CLOSED rather than merged. Merge once every bot signs off (Codex `LGTM`, CodeRabbit no actionable comments, Sourcery LGTM/skipped) AND CI is green AND the user confirms. Trigger shorthands the user actually types: "comments", "ci & comments", "ci失敗とcomments", "CIとコメント", "loopしてokになるまで" — all mean: infer the PR from the current branch, fetch new bot/CI feedback, triage, fix, loop until green.
---

# GitHub Review Loop

Reactive sibling of `codex-cross-review`. That skill drives a local
`codex exec`; this one reads what the **GitHub-side** review bots
already posted (via GitHub Actions, GitHub Apps), responds, and waits
for them to come back with the next iteration.

The contract assumes at least one bot posts a `CODEX VERDICT: LGTM`
or `CODEX VERDICT: CHANGES REQUESTED` line on every push. If a repo
has neither Codex auto-review nor CodeRabbit nor Sourcery wired up,
this skill has nothing to react to — use `codex-cross-review`
instead.

## Inputs

PR URL (`https://github.com/<owner>/<repo>/pull/<N>`) or number. If
only a number, infer owner/repo from `gh repo view --json
nameWithOwner`. With no arg, infer the PR for the current branch —
open-PR-first, since this loop targets open PRs:
`gh pr list --head <branch> --state open --limit 1 --json number`,
falling back to `--state merged` only if nothing is open.

## Setup (once)

1. `date -u +%Y-%m-%dT%H:%M:%SZ` — capture iteration start time.
2. `gh pr view <N> --json state,headRefName,baseRefName,mergeable,isDraft,statusCheckRollup,headRefOid`
   — confirm OPEN & not draft. Record `headRefOid` → `LAST_PUSHED_SHA`
   so the loop can tell when a new push has produced a fresh CI run.
3. `gh pr checkout <N>` — local working copy.
4. Record `LAST_KNOWN_MAIN = git rev-parse origin/main`.
5. Read repo `CLAUDE.md` if present — every fix has to honour it.
6. Confirm `gh auth status` is logged in. If not, stop and report.

## The Loop (ends on two consecutive clean rounds — no iteration cap)

State file `/tmp/gh-review-loop-<N>/iteration-<k>.json` records
findings + decisions per iteration so the run is auditable.

### The ledger — and why it has to live on the PR

Keep `/tmp/gh-review-loop-<N>/ledger.md`: every finding raised so far
and what happened to it. One row per finding, written in step C while
the evidence is still in hand.

```markdown
| # | iter | bot | finding (one line) | disposition | why / where |
|---|------|-----|--------------------|-------------|-------------|
| 1 | 1 | codex | `parseRange` accepts a reversed span | FIXED | commit a1b2c3d, test `test_range.ts:42` |
| 2 | 1 | CR | suggests memoising `buildIndex` | REJECTED | called once per boot; measured 0.4 ms |
| 3 | 2 | sourcery | extract the nested ternary | DEFERRED | touches a file this PR does not own — issue #123 |
```

Dispositions: `FIXED` / `REJECTED` / `DEFERRED` / `REOPENED`. A
`REJECTED` row must carry the evidence that refuted it, not just the
verdict — "false positive" tells the next round nothing and invites the
finding straight back.

**The difference from `codex-cross-review`: you cannot put this in the
bots' prompt.** They are GitHub Apps and workflows; their instructions
are not yours to write. What they *do* read is the PR thread. So the
ledger only works here if it is **posted as a PR comment**, refreshed
each iteration:

````bash
gh pr comment <N> --body-file - <<'EOF'
## Review ledger — after iteration <k>

Findings raised so far and what happened to each. Re-flagging a `FIXED`
or `REJECTED` row is welcome **if the resolution is wrong** — say which
row and what is wrong with it.

<the table>
EOF
````

Keeping it only in `/tmp` gets you the bookkeeping and none of the
benefit: the bot re-reviewing the next commit sees the diff and the
thread, never your scratch files.

**A repeat finding is a signal, not noise.** It means either the row's
one-liner does not describe what the bot actually meant, or the
resolution genuinely did not hold. Re-read your own row before
dismissing the repeat — the cheapest explanation is that you summarised
the finding into something you had already fixed.

### Iteration step A — wait for the bots to post their reviews

After every push, the bots run asynchronously. Don't fetch comments
prematurely — you'll see stale findings from the previous commit.

Wait for the Codex review workflow. Don't hardcode its name — it
varies per repo. Discover it once via `gh workflow list` and store
it in a variable:

```bash
# Discover the Codex review workflow name (once per run)
CODEX_WORKFLOW=$(gh workflow list --json name \
  --jq '.[] | select(.name | test("codex"; "i")) | .name' | head -1)

# Get the run ID for this PR's latest codex review job
RUN_ID=$(gh run list --workflow "$CODEX_WORKFLOW" --branch "$HEAD_REF" \
  --limit 1 --json databaseId,headSha --jq \
  ".[] | select(.headSha == \"$LAST_PUSHED_SHA\") | .databaseId")

# Block until it's done; cancel-in-progress means the latest one wins
until [ "$(gh run view "$RUN_ID" --json status --jq .status)" = "completed" ]; do
  sleep 12
done
```

CodeRabbit posts via GitHub App, not a workflow run — no exact
"is it done" signal. Use a 30-90 s grace after the Codex job
finishes; CR usually lands within that window. Sourcery is even
more variable but rate-limited frequently.

**Collect every bot's findings for this commit before you fix anything.**
You cannot tell a GitHub App to batch its output the way you can
instruct a local `codex exec` — so the batching has to happen on the
receiving side. Findings arrive staggered: Codex at 40 s, CodeRabbit at
90 s, Sourcery whenever. Reacting to the first arrival gives you a push
per bot, and each push starts a fresh review round on a commit the other
bots never finished reading — the loop inflates its own round count and
every bot re-reviews a moving target.

Wait out the grace window, gather all three sources (step B), then
respond once. If a late finding lands after you have pushed, it belongs
to the next iteration; do not amend mid-round.

**A bot that did not review is not a bot that approved.** Rate limits
are the common case — Sourcery's weekly diff-character cap, CodeRabbit's
per-hour limit. Record the absence explicitly in the iteration state
(`sourcery: rate-limited, no review`) and carry it into step G, where a
missing signal cannot count toward a clean round.

### Iteration step B — fetch this iteration's review

Filter by author + (created_at > iteration start):

```bash
mkdir -p /tmp/gh-review-loop-<N>
# `github-actions[bot]` posts all sorts of unrelated CI comments, so it
# only counts as a reviewer when the body carries the `CODEX VERDICT:`
# marker. If your repo's Codex workflow posts inline findings as
# github-actions WITHOUT the marker, widen the inline filter for that repo.
gh api "repos/$OWNER_REPO/issues/$N/comments" --paginate \
  --jq "[.[] | select((.user.login | test(\"codex|coderabbit|sourcery\"; \"i\")) \
         or ((.user.login | test(\"github-actions\"; \"i\")) and (.body | contains(\"CODEX VERDICT:\")))) \
       | select(.created_at > \"$ITER_START\") \
       | {user: .user.login, app: .performed_via_github_app.slug, created: .created_at, body}]" \
  > /tmp/gh-review-loop-<N>/top-<k>.json

gh api "repos/$OWNER_REPO/pulls/$N/comments" --paginate \
  --jq "[.[] | select((.user.login | test(\"codex|coderabbit|sourcery\"; \"i\")) \
         or ((.user.login | test(\"github-actions\"; \"i\")) and (.body | contains(\"CODEX VERDICT:\")))) \
       | select(.created_at > \"$ITER_START\") \
       | {user: .user.login, app: .performed_via_github_app.slug, created: .created_at, path, line, body}]" \
  > /tmp/gh-review-loop-<N>/inline-<k>.json

gh api "repos/$OWNER_REPO/pulls/$N/reviews" --paginate \
  --jq "[.[] | select(.user.login | test(\"coderabbit|sourcery\"; \"i\")) \
       | select(.submitted_at > \"$ITER_START\") \
       | {user: .user.login, state, submitted_at, body}]" \
  > /tmp/gh-review-loop-<N>/reviews-<k>.json
```

The verdict marker for the loop's machine signal: a top-level comment
that **starts** with `CODEX VERDICT: LGTM` or `CODEX VERDICT: CHANGES REQUESTED`.
Find the most-recent one in `top-<k>.json`.

Author identification trap: `codex` may post as either
- `github-actions[bot]` (when the workflow uses `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` → standard CI auth),
- the actual user via `chatgpt-codex-connector` GitHub App (when codex CLI uses its own auth via `~/.codex/auth.json`).

If you see a `chatgpt-codex-connector`-signed comment dated BEFORE
the latest push, it's probably from a manual `codex exec` session, not
the CI run. Don't treat it as the latest verdict.

### Iteration step C — triage and skip boilerplate

Drop:
- CodeRabbit walkthrough / sequence-diagram / poem / "Estimated effort" sections.
- CodeRabbit "rate limit exceeded" notices — treat as "no review this iteration".
- Sourcery rate-limit messages — same.
- Any bot's marketing/CTA section.

For each real finding, decide:
- **MUST-FIX** — bug, security, type hole, data loss, regression.
- **VALID-NIT** — small quality / readability win, no downside.
- **FALSE-POSITIVE** — bot misread the diff or repo conventions.
- **DEFER-TO-FOLLOWUP** — real but out of this PR's scope; record as
  a follow-up issue.

Apply MUST-FIX + VALID-NIT immediately. For FALSE-POSITIVE / DEFER,
post a short reply on the PR explaining why so the next iteration
doesn't re-flag.

**Write each finding into the ledger as you dispose of it**, not at the
top of the next round. Reconstructing it later is how rows end up saying
"false positive" with no reason attached — which is exactly the row that
brings the finding back. Re-post the refreshed ledger comment before
step F's push, so the bots reviewing the new commit see it.

**Don't trust the bots blindly.** Every finding must pass your own
review against the actual code. Bots are starting points, not
ceilings — note any issues you observe that the bots missed and fix
those too, attributed honestly in the commit message ("observed
during Claude review, not flagged by Codex").

### Iteration step D — local checks

After any code change, run the project's mandated checks (derived
from `CLAUDE.md` or conventional defaults):

- `yarn format` (Prettier)
- `yarn lint`
- `yarn typecheck`
- `yarn build`
- `yarn test` (skip e2e in-loop; CI catches e2e regressions)

If any check fails, fix and retry before pushing. Do not push a red
build into the loop — it confuses the bots' review thread.

### Iteration step E — sync main

```bash
git fetch origin main
NEW_MAIN=$(git rev-parse origin/main)
if [ "$NEW_MAIN" != "$LAST_KNOWN_MAIN" ]; then
  git merge origin/main --no-edit
  # Resolve conflicts: prefer your edits in files you touched this
  # iteration, but re-apply main-side logic. Pause for the user if
  # the conflict is semantic and unclear.
  LAST_KNOWN_MAIN=$NEW_MAIN
  # Re-run local checks after the merge — main may have changed contracts.
fi
```

### Iteration step F — commit + push

- `git add` only intentionally-touched files. Never `git add -A`.
- Commit message: `fix: address CR/Codex review iter-<k>` — list
  accepted findings in the body, attribute by reviewer. Use the
  environment's standard Co-Authored-By trailer for the current model.
- `git push` (no force).
- Capture the new HEAD SHA → `LAST_PUSHED_SHA` so step A of the
  next iteration knows which CI run to wait on.

### Iteration step G — decide whether to loop

Inspect this iteration's signals:

| Signal | Action |
|---|---|
| Codex `CODEX VERDICT: LGTM` + no other actionable bot comments + no issues YOU spotted | **clean round** — see the exit rule below; one is not enough |
| Codex `CODEX VERDICT: LGTM` + you found real issues | not clean. Fix them anyway, push, next iteration (Codex will re-verify) |
| Codex `CODEX VERDICT: CHANGES REQUESTED` | next iteration |
| CodeRabbit posted MUST-FIX comments only | next iteration |
| A bot was rate-limited / posted nothing | not clean. Its silence is not a sign-off — see below |
| No Codex run at all (workflow misconfigured / failed) | escalate to user — don't pretend the silence is approval |
| Next iteration is a multiple of 5 | run the checkpoint first (*Every fifth round*), then step A |
| The round established the PR should not exist | stop and take the close path (*Closing the PR*) — this outranks a pending LGTM |

### Exit: two clean iterations in a row

**One clean round is not convergence — it is a round that happened to
find nothing.** A fix pushed in response to round N is reviewed for the
first time in round N+1, and by then most findings are about the loop's
own work rather than the original diff. So the loop ends when **two
consecutive iterations are clean, with the second reviewing a head the
first has already seen** — no new commit between them, or if there was
one, the count starts again.

Concretely: a clean round with commits pushed in it does not count as
the first of the two. Push nothing, re-trigger the bots on the unchanged
head, and get a second clean round.

Re-triggering without a commit is bot-specific: CodeRabbit takes comment
commands (`@coderabbitai review`; run `@coderabbitai help` in a PR
comment to confirm the current set), and a workflow-driven Codex review
can be re-run with `gh run rerun <run-id>`. If a bot genuinely cannot be
re-triggered without a push, say so in the report rather than counting
its previous round twice.

**A silent bot never contributes to a clean round.** Rate-limited,
crashed, or not configured — all three look identical from the thread,
and none of them is approval. Either wait for the limit to clear and
re-trigger, or record in the final report exactly which reviewer never
saw the final head. A "converged" PR that two of three reviewers read is
a fact the human deserves to be told.

### There is no cap

**The loop runs until two consecutive clean rounds, however many that
takes.** No round budget, and no separate rule for small PRs — a one-line
diff that cannot converge in five rounds is not a small change, it is a
disagreement about something the diff does not show, and stopping there
hides exactly the thing worth finding.

**Do not stop mid-loop to ask the user whether to continue.** "This is
taking a while", "we are at round 12", and "the remaining findings look
minor" are not reasons to stop — they are the loop working. The loop ends
early for exactly these, and nothing else:

1. **A decision that is genuinely the user's** — see below.
2. **The bots cannot be reached at all** (workflow misconfigured, auth
   failed, every reviewer rate-limited with no reset in sight).
3. **A semantic merge conflict** that step E says to escalate.

If the loop passes ~10 rounds without two clean in a row, say so and keep
going — but read the pattern out loud first. Findings that keep arriving
in the same shape mean the fix enumerates bad cases instead of stating
the rule; findings that arrive in new shapes each round mean the change
is bigger than the PR admits and may want splitting — or closing.

### Stopping for the user

The exception to "do not stop" is narrow: a question the code cannot
settle, where proceeding either way would be guessing at intent.

- **The loop concludes the PR should be closed** — bring the
  recommendation and the evidence, never the action.
- **The merge go-ahead**, as it always was.
- **A finding whose resolution is a product or policy decision** — which
  of two valid behaviours is wanted, whether a breaking change is
  acceptable, whether a deferred item blocks a release. Post the options
  and what each costs; do not pick one and call it converged.
- **A conflict whose correct resolution is not derivable** from either
  side's history.

Everything else — including a finding you flatly disagree with — is
resolved inside the loop by posting the rebuttal and letting the next
round answer it. When you do stop, say which of these it is and what
specifically you need decided.

### Every fifth round, re-read the whole PR

Findings compound. By round 5 the conversation is mostly about the loop's
own output, and a loop can converge beautifully onto the wrong thing — a
rule refined for four rounds that should not exist, tests grown around a
behaviour the PR was never supposed to have. Round-by-round review cannot
see this, because each round only ever looks at the delta.

At iterations **5, 10, 15, …**, before step A, stop reacting and read the
PR whole (`git diff origin/main...HEAD`), as if seeing it for the first
time:

- Does the diff still do what the PR title and body say? If the body now
  describes a different change, the body is stale or the PR has drifted
  — name which.
- How much of the diff is original work versus bot-response additions? A
  PR that is now majority review-response is a PR whose centre of gravity
  moved.
- Is anything there only because a bot asked, and no longer justified on
  its own? Removing it is a legitimate outcome.
- Would you approve this diff if it arrived fresh today, with none of the
  thread attached?
- What is the single largest remaining risk?

Post the answer as one comment (`## Checkpoint — round <k>`), and ask the
bots for a **full** re-review rather than an incremental one where they
support it (`@coderabbitai full review` — confirm against
`@coderabbitai help`). If the repo also has the `codex` CLI available,
`codex-cross-review`'s checkpoint prompt gives you the second opinion
this loop otherwise lacks.

A checkpoint produces no verdict, so it neither counts toward the two
clean rounds nor resets them — it sits between rounds. But if it changes
direction (scope cut, split, close), the count **does** start over:
what the earlier sign-offs approved is no longer what will merge.

### Closing the PR is a legitimate outcome

A review loop is not obliged to end in a merge. Sometimes the thread
establishes that the change should not exist, and the protocol has to be
able to say so — otherwise every PR converges by construction, and the
loop's only possible output is approval of whatever it started with.

Recommend closing when the thread has established one of these, with
evidence on the PR:

- **The premise is false.** The bug does not reproduce, the slow path is
  not hot, the platform behaviour it works around was fixed upstream. A
  PR fixing something that is not broken has no correct version.
- **The right fix is somewhere else.** The change treats a symptom and
  the loop located the cause in another layer. Say where, and link the
  issue that replaces this.
- **It has been superseded.** Main moved during the loop and now does
  this, or does something incompatible that arrived with more context.
- **The cost exceeds the benefit, and the loop measured both.** Not "this
  is getting complicated" — an actual accounting.
- **It should be split, and nothing is left after splitting.** If every
  part belongs in its own PR, this one is a container, not a change.

Closing is the user's call, so bring it decided:

1. **Post the case on the PR first** — what was believed at the start,
   what the loop established, which reason applies, and links to the
   findings and commits that got you there.
2. **Put the recommendation in front of the reviewers** before the user.
   A close argued by one party alone is the unilateral conclusion this
   loop exists to prevent; give the bots a round to answer it.
3. **Say what replaces it**: the issue to open, the smaller PR to cut, or
   nothing at all — and if nothing, say that explicitly, because "closed
   and forgotten" and "closed because it is already handled" look
   identical six months out.
4. **Then stop and ask the user**, recommendation in one line. Never run
   `gh pr close` on your own judgement.

A close that arrives at round 9 is not a wasted loop. The rounds are what
established the premise was false; without them it would have merged.

## CI monitoring (continuous, parallel to the loop)

Between every iteration AND continuously while waiting on CI:

```bash
gh pr checks <N> --json name,state,conclusion,link
```

CI failures are part of the loop, not separate from it:

1. Identify the failing job.
2. `gh run view <run-id> --log-failed` to read logs.
3. Reproduce locally if possible.
4. Fix → local checks → commit (`fix: CI <job-name> <reason>`) → push.
5. The push re-triggers Codex auto-review, which becomes the next iteration's input.

Do not ignore "unrelated" failures. A pre-existing main failure that
broke during an unrelated merge IS now your problem if it blocks
your branch's CI.

## Merge (once converged)

1. If the diff touches UI files, offer a manual click-through
   before merging (headless-Chrome screenshot flow → `rules/preview.md`).
2. Verify in chat with the user: "Codex LGTM + my evaluation clear +
   all CI green. Ready to merge?"
3. On confirmation: `gh pr merge <N> --merge --delete-branch`
   (follow the repository's merge convention; confirm with the
   user before squashing).
4. After merge: `git checkout main && git pull`, confirm
   `mergeCommit.oid`, report final state.
5. If `pr-merge-tidy` skill is available and the PR linked an issue
   or introduced a plan file, suggest running it as a follow-up.

## Safety rules (always)

- Never skip local checks. Never `--no-verify` / `--no-gpg-sign` / `--force`.
- Never apply a bot suggestion blindly. Every fix passes through
  your own review first.
- If you disagree with a bot, SAY SO in a reply comment with
  reasoning — silent disagreement breaks the loop's signal.
- Sync main before every push.
- Never commit secrets. Never include `.env` / credential files.
- If you find issues bots missed, attribute them honestly in the
  commit ("observed during Claude review, not flagged by Codex").
- Never `gh pr close` on your own judgement, and never merge one. Both
  are the user's call; you bring the recommendation with its evidence.
- The ledger is a memory aid, never an authority. A `REJECTED` row does
  not make a repeat finding wrong — it makes the row worth re-reading.
- Never let a bot's silence stand in for its approval, in the loop or in
  the report.
- Respect project-specific rules in `CLAUDE.md` — they override
  these defaults on conflict.
- If the pre-commit hook fails on an UNRELATED main-side breakage,
  fix it inline (smallest possible patch) and call it out clearly
  in the commit message. Don't bypass the hook.

## What "OK to merge" means from Claude's side

Not just "the bots stopped complaining." Claude's own OK requires:

- No MUST-FIX findings remaining (from any bot or from your own reading).
- No related issues in adjacent code that the diff invites but
  doesn't fix (deliberate deferrals must be posted as PR replies
  with rationale, not silent).
- All project checks pass locally.
- Test coverage matches the change shape — new logic has at least
  one test asserting the new behaviour.
- i18n / a11y / security conventions from `CLAUDE.md` are honoured.

Only then is it ready for the user merge confirmation.

## Reporting to the user

After every iteration, give a 3-4 line status:

- Iteration `<k>` (no cap — running to two consecutive clean rounds)
- Bot signals this iteration: `Codex: LGTM/CHANGES (N)`, `CR: clean/N nits`, `Sourcery: LGTM/rate-limited`
- What you changed this iteration (1 line)
- Clean-round count: `0` / `1 of 2` — and if it reset, why
- CI status at this moment

This is a status line, not a question. Do not end it with "shall I
continue?" — the loop continues unless one of the three early-exit
conditions fired, and asking invites a stop the protocol does not want.

Final report on merge: PR number, merge commit SHA, total iterations,
**which reviewers signed off on the final head and which never saw it**,
notable disagreements with bot findings if any.

Final report on a close recommendation: which reason applies, the
findings that established it, what replaces the PR, and how the bots
answered the recommendation.

## Novelty-diff review (on request)

When the user asks "review and tell me what CodeRabbit/bots missed"
(e.g. 「code rabbitのコメントにない指摘ある？」):

1. Run an independent review of the full PR diff — don't anchor on
   the bot threads.
2. Dedupe your findings against ALL bot comments (top-level, inline,
   review bodies).
3. Present only the novel findings in chat, ranked by severity.
4. Post them as PR comments only after the user confirms.

## When NOT to use this skill

- The repo doesn't have any review bots wired up → use
  `codex-cross-review` (drives codex CLI locally instead).
- The PR is already merged → use `pr-merge-tidy` to sweep up the
  trailing chores, and open follow-up PRs for what was missed.
- Many PRs need triage at once → use `pr-babysit` for the
  scan, this skill for each individual PR you decide to chase.
