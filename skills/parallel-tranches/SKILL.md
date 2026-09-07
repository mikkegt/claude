---
description: Rules and paid-for failure modes for working ONE backlog issue (a lint backlog, a migration, an audit) with several agents in parallel git worktrees. Read BEFORE running more than two agents at a time, or when the user says "並列で回して", "worktree で分担", "エージェント複数でこの issue を潰して". Covers claiming entries so two agents don't collide, the collision check a merged PR is invisible to, worktree isolation, measuring under load, and resuming an agent that died mid-flight.
---

# Parallel tranches — one backlog issue, several agents

A tracking issue holding a list of entries invites several agents at once. What breaks is never
the code; it is the **coordination**. Every rule below was paid for.

## The rules

### Before starting

- MUST **claim the entry on the issue before the work starts** — a comment naming what will be
  touched as a **function or line range**, not just a file. Two tranches at opposite ends of one
  file is fine; two in one function is not, and only a specific claim tells them apart.
  Dispatching a batch → one comment covering all of them, plus a "not claimed" line so the
  remaining surface stays readable
- MUST run the collision check as **two** commands: `gh pr list --state open` **and**
  `git log origin/main --oneline -20 -- <file>`. A PR that merged an hour ago appears in neither
  the open list nor the working tree
- MUST confirm the target is **reachable** before extracting from it — `grep` for the caller,
  `git log --all -S "<symbol>"`. Extracting from an orphan gives it named exports and tests, and
  argues to the next reader that it is load-bearing
- **One file per agent.** NEVER two agents in one file, whatever the line distance between them

### How many

- MUST check `uptime` before adding a worktree or an agent, and MUST NOT add one while the load
  average is already high — it is the *existing* work that pays, in timeouts that then have to be
  re-run and re-judged. Budget against cores, not against ambition
- "The machine is loaded" MUST stop new work, not merely slow it. Reviews of what is already in
  flight continue, sequentially

### Isolation

- Each agent MUST get its own git worktree. `node_modules` MUST be symlinked rather than installed
  per worktree — and the symlinks MUST be removed before the agent finishes
- NEVER run a command that mutates shared state from a worktree — `prisma generate` above all,
  when several tranches share one generated client

### Measuring under concurrency

- A timeout at high load is the load, not the change. MUST re-run the file standalone
  (`--testTimeout=120000 --hookTimeout=120000`) before concluding a failure is yours, and MUST say
  which failures were re-run
- A mutation sweep MUST assert the file matches a pristine copy **before** each mutation as well as
  after each restore

### When an agent dies mid-flight (session limit, crash)

- MUST resume rather than restart — the worktree holds the work. MUST re-establish state first
  (`git status`, `git log`, re-run the lint) and MUST verify the source matches the intended
  version before measuring anything: an interrupted sweep may have left a mutation behind
- MUST re-sync `origin/main` on resume and re-run the gates on the merged result — CI runs against
  a combination nobody has executed

## What the rules cost


The setting throughout is a real one: a `sonarjs/cognitive-complexity` backlog
of 65 entries in the ≤20 band, worked as one-function-per-PR tranches, four to five agents at a time,
each in its own git worktree, each producing a PR that then went through a Codex review loop before
merging. Over a day it took the band from 65 to 32 and the repo total from 163 to 131. Everything
below went wrong at least once along the way.

## The coordination failures

### A merged PR is invisible to every check you were running

Each tranche opened with a collision check: `gh pr list --state open`, then `gh pr diff <n> --name-only`
on the plausible ones. One tranche picked `backend/src/ktap/extract.ts`, worked its casts, and found
at the end that a PR had **merged an hour earlier** taking that whole area from 50 casts to 0. It was
not in the open list, because it was closed. It was not in the working tree, because the branch had
been cut before the merge.

The missing command is `git log origin/main --oneline -20 -- <file>`. It costs nothing and answers
the question the open-PR list cannot.

### "Stop and report" needs a scope, or an agent has to invent one

A later tranche found an open PR editing the same file — the last 120 lines, ~400 lines from anything
it was touching. Its brief said "if an open PR touches this file, stop and report", so it had to
decide alone, mid-flight, whether that instruction was aimed at duplicated work or at any overlap at
all. It chose to proceed and flagged the judgement, which was right, but nothing in the record said
who had arrived first or what either party had claimed.

Hence the claim: a comment on the issue, before the work, naming the **function or line range**. Two
tranches at opposite ends of one file is fine. Two in one function is not. Only a specific claim can
distinguish them, and the claim is also what a reviewer reads to see whether the two PRs need
ordering.

### When the mainline decides your open question, the tests are the part that must move

The collision does not always look like duplicated work. Sometimes the mainline answers a question
your branch had deliberately *deferred* — and then your branch's tests are pinning the answer it
rejected.

> A tranche found two query-string casts it could not remove without changing the API: narrowing them
> answers `undefined`, which drops a filter and skips a 404 check. Rather than decide that inside a
> refactor it filed the question as its own issue and **pinned the existing behaviour with two
> tests**, which is the right move. Three days later the mainline decided it the other way: a repeated
> parameter now means *absent*, because answering `?projectId=a&projectId=b` with `'a'` silently
> scopes a listing to one of two projects the caller named.

Merging then produces a branch whose helper is redundant and whose tests assert the superseded rule.
Deleting all of it is one wrong answer; keeping the tests as they are is the worse one, because a
suite that records what used to be true is read by the next person as a specification.

What survives is the coverage at a level the mainline's own tests cannot reach — here the **route**,
where dropping `projectId` also skips the ownership lookup, which the extracted helper's unit tests
cannot see. Rewrite those to the new rule and break-verify them against the *old* one: a single
mutation restoring the previous semantics should turn exactly those tests red and nothing else.

## The reachability failures

### `knip` answers a different question than the one you are asking

The gate after the first orphan (`clawBinary.ts` — never imported in the repository's history, and an
extraction was written for it before anyone checked) was `yarn knip --include files` before
extracting. It does not report:

- **`FileViewer.tsx`**, whose only remaining reference is a *type-only* import in `App.tsx`. A type
  import keeps a file "used" at file granularity while the component is never rendered — the ref that
  import typed had been a permanent `null` since the commit that removed the last `<FileViewer />`, so
  three `.refresh()` call sites had been no-ops for two months.
- **`folderTree.ts`, `fileViewerAction.ts`, `FolderPickerModal.tsx`**, whose only readers are their own
  `*.test.ts(x)` — and `knip.jsonc` declares test files as *entry points*, correctly, because a helper
  only a test uses is not dead. The consequence is that a module whose last non-test reader
  disappeared can never be reported.

So knip answers *"is this file imported"*. The question is *"can this code be reached"*. For a `.tsx`
target the difference is one grep: `grep -rn "<ComponentName"`.

Two tranches had already extracted tested rules out of that unrendered component before anyone
noticed. Both are now importable only from their own test files.

## The measurement failures

### A leftover `node_modules` symlink makes the repo lint twice

Agents symlink the primary checkout's `node_modules` into their worktree rather than installing —
correct, and much faster. If the symlink survives the agent, the *next* `npx eslint .` from the repo
root walks `.claude/worktrees/agent-*/` too and lints two or three whole copies of the repository.

Observed twice. The first time it reported 5,130 errors and a nonsense rule breakdown; the second
time it reported the backlog as **zero remaining**, which is exactly the shape of a result nobody
questions. Remove the symlinks in the agent, and pass `--ignore-pattern '.claude/**'` when measuring
from the root.

### A dismissed CodeQL alert does not survive being moved

Extraction is exactly the operation that breaks a security alert's identity, and the failure is
one-directional: the alert comes **back**, red, on the pull request that touched nothing.

> A tranche extracted an `fs.stat` out of a 200-line method into a small named one. CodeQL went red
> with one new high-severity `js/path-injection`. It was not new. It was the same rule, the same
> sink, the same four sources, the same ten flow steps as an alert on the default branch — which a
> human had **dismissed as a false positive three weeks earlier**. The line's indentation and its
> enclosing function had both changed, so its `primaryLocationLineHash` changed, GitHub could not
> match the two, and it minted a fresh alert with no dismissal attached.

The check that settles it in one command is comparing the two analyses' `codeFlows`, not reading the
code:

```bash
gh api repos/<owner>/<repo>/code-scanning/analyses/<id> -H "Accept: application/sarif+json"
```

Identical sources plus identical step count means the flow did not change; only its address did.

Two API details cost a wrong answer on the way there, both worth knowing before you assert anything
about a CodeQL result:

- **`code-scanning/alerts` pages.** Without `--paginate` the file looked like it had *one* open alert
  of that rule. It had sixteen, plus six dismissed. Every conclusion drawn from the short list was
  about a different alert.
- **A pull request's analysis is diff-informed.** The branch analysis reported 254 results; the PR's
  reported 1. So "the PR only has one finding in this file" is not a statement about the file — it is
  a statement about which findings GitHub chose to recompute.

### A stale shared Prisma client is not your change

Several worktrees share one `node_modules`, hence one generated Prisma client. When `main` adds a
model, every worktree's `tsc` reports errors in files nobody touched. Three separate tranches hit
this; the correct handling — which one of them worked out and the others then copied — is:

- do **not** run `prisma generate`, because it mutates state the other tranches are using;
- confirm the failure reproduces with your own change reverted;
- say so in the report, and note that CI regenerates the client before typechecking.

### A timeout at load average 120 is the load

Five agents plus three Codex reviews took the machine to a load average of 120 on a laptop. Under
that, `vitest`'s 10s hook timeout and 15s test timeout fire on tests that have nothing to do with any
change in flight — and they fire on a *different* file each run, which is the tell. Re-running the
same three files standalone with `--testTimeout=120000 --hookTimeout=120000` turned 3 failures into
37 passes.

This is why the load check is a rule rather than a courtesy: every agent added past the machine's
capacity does not merely go slower, it makes the *existing* agents produce failures that then have to
be re-run and re-judged, one at a time, by hand.

### A concurrent sweep can put a mutation in your file

A mutation sweep edits production code dozens of times and restores it after each. `git status` cannot
distinguish your mutation from a sibling's. One agent found a guard it had reasoned was redundant
scoring 603 differences, and a `diff` against a saved copy showed a mutation **it had never applied**.

The fix is cheap and belongs in every sweep: assert the file matches a pristine copy **before**
applying each mutation, not only after restoring it. A stray mutation left in the tree reads as *more*
coverage — the next case scores against an accumulating edit — which is the direction that does not
announce itself.

## The verification failures

These are not specific to parallelism, but parallelism is where they surfaced, because five agents
running the same method produce five samples of its weak points.

### A harness over a private function can score the rule against itself

A tranche comparing a module-private collector reported 0 differences three times over. The collector
was not exported, so the harness had *reimplemented* it — and was comparing that reimplementation with
itself. Only a second harness entering at the caller's exported boundary produced counts that moved.

If the function under comparison is private, enter at the caller as well. A zero from a harness that
cannot reach the code is indistinguishable from a zero that means equivalence.

### Removing a cast changes behaviour, and query parameters are where it shows

`?status=a&status=b` arrives at Express as an **array**. A `status as string` cast passed that array
straight through — to Prisma, to `parseInt`, to whatever came next. Replacing the cast with a `typeof`
guard answers `undefined` instead, so a request that used to 500 now succeeds *unfiltered*, and a
`?limit=5&limit=6` that used to mean 5 now means the default.

There is no version of "remove this cast" that preserves the old answer, because the cast is what
produces it. The resolutions that are honest: keep the cast and say why, or make the change and **put
it in the PR title**, since the body is not what survives being read from a PR list. What is not
honest is a title that says refactor over a diff that changes an API.

### For genuinely dead code, "restore it and watch a test fail" cannot be satisfied

A reviewer asked a deletion to be verified the way the method verifies removals: put the branch back,
watch something go red. The deleted branch was `if (ref.current) { … }` where `.current` was
permanently `null`. Restoring it restores a statement that does nothing — no test can separate the two
versions, and if one could, the branch would have been reachable and the deletion wrong.

What *can* be pinned is the invariant the deletion leans on. There, a no-op `() => {}` had to stay in
`App.tsx` because a listener's effect opens `if (!onFileWritten) return` — the prop is a switch, and
deleting the empty function as dead weight would silently switch the listener off. Two tests, one
mutation, and the thing a future cleanup would break is now guarded.

## The pattern worth naming

Across roughly twenty tranches, the single most common review finding was **not a defect in the code**.
It was a defect in the *sentence explaining why the code is safe*: an equivalence claimed for "every
shape" that held only for the shapes one caller can produce; a `[object Object]` that nothing
stringified; a "the only place this is observable" that was not observable there at all.

The comment justifying a change is the least-tested artefact in a PR, and it is what the next reader
believes. Check it against the code as carefully as the code.
