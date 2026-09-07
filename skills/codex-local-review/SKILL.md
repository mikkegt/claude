---
description: Local Codex review of a diff BEFORE it becomes a PR — no GitHub round-trip. Runs Codex read-only over the working-tree or branch diff, forces an explicit verdict, then YOU evaluate each finding and apply only what survives. Use when the user says "localでcodexレビュー", "codexに見てもらって", "PR前にcodexで確認", "これ副作用ない？安全？", "second opinion", or before committing anything sensitive (payments, auth, security rules, irreversible/destructive operations). For an OPEN GitHub PR where Codex posts comments and you converge over iterations, use codex-cross-review instead.
---

# Codex Local Review

A pre-PR second opinion. Codex reviews the local diff read-only; you evaluate its findings with full context. Nothing is pushed, nothing is posted to GitHub.

## When this, not codex-cross-review

| | codex-local-review | codex-cross-review |
| --- | --- | --- |
| Target | local diff (uncommitted or branch) | open GitHub PR |
| Codex writes | nothing (read-only) | inline + top-level PR comments |
| Needs network/GitHub | no | yes |
| Use for | pre-commit gate, "is this safe?" | full convergence loop + CI + merge |

`review-code` is the third option: your own review, no external tool. Use it when `codex` is not installed, or as the pass you run BEFORE handing the diff to Codex — running yours first means Codex's findings arrive against a diff you already understand.

## Steps

### 1. Scope the diff

Decide explicitly and tell the user what you're reviewing:

- uncommitted work → `git diff` (and `git diff --staged` if staged)
- a branch → `git diff <base>...HEAD` (resolve base via `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else `main`)

**Make sure the diff contains ONLY the intended change.** If a repo-wide formatter or an unrelated edit polluted the working tree, revert that noise first — Codex reviewing 50 reformatted files produces garbage and buries the real change.

### 2. Preflight

`command -v codex` — if missing, stop and tell the user to install `@openai/codex`.

### 3. Run Codex read-only

`--sandbox read-only` is mandatory: this is a review, Codex must not edit files.

```bash
codex exec --sandbox read-only "Review ONLY the uncommitted change in this repo. Run \`git diff <paths>\` to see it, and read the surrounding code for context. Do NOT modify any files.

Context: <what the change is for, and WHY — Codex cannot infer intent from the diff>

Evaluate strictly:
1. <specific question 1>
2. <specific question 2>
...

End with a line 'CODEX VERDICT: LGTM' or 'CODEX VERDICT: CHANGES REQUESTED' + bullet list."
```

Three things make or break this call:

- **Give it the intent.** A diff alone doesn't say what invariant you're protecting. State the bug being fixed and what must stay unchanged.
- **Ask specific questions, not "review this".** Generic prompts get generic answers. Ask the things you actually fear: is the happy path byte-identical? does a retry double-execute a side effect? does removing this throw swallow an error that should fail? is the guard nesting right?
- **Force the verdict marker.** Without the contract you get prose you can't act on.

Codex output is long — `| tail -60` to get the findings + verdict.

### 4. YOU evaluate every finding

Not a passive apply step. For each finding:

1. **Necessity** — real bug, style preference, or false positive? Verify against the code before accepting.
2. **Blast radius** — same pattern elsewhere? A one-site fix that leaves siblings broken is worse than the finding.
3. **Side effects** — would the suggested fix break callers or regress a test?
4. **Gaps Codex missed** — read the diff yourself. Codex is a starting point, not a ceiling.

Categorise MUST-FIX / VALID-NIT / FALSE-POSITIVE / DEFER. Apply MUST-FIX + cheap VALID-NIT. If you disagree, say so with reasoning — don't silently ignore.

### 5. Re-run if you changed logic

Material changes → run step 3 again so the verdict covers what you'll actually ship. Cosmetic changes → don't bother.

### 6. Local checks, then report

Run the project's gates (`build` / `lint` / `typecheck` / tests per its CLAUDE.md). **Do not run a repo-wide formatter unless the repo is already format-clean** — otherwise it rewrites unrelated files and pollutes the PR.

Report to the user:

- what was reviewed (scope of the diff)
- Codex verdict: LGTM / CHANGES REQUESTED (N findings)
- your evaluation: what you accepted, rejected (with reason), and anything Codex missed
- residual risks / assumptions the change does NOT address
- gate results

Then ask whether to commit/PR. Never merge or push from this skill — it is a review gate, not a delivery pipeline.

## Honesty rules

- If you found issues Codex missed, attribute them to yourself, not Codex.
- Report a Codex LGTM as an LGTM — but if your own reading found a MUST-FIX, say so and fix it; Codex agreeing is not permission to ship a bug.
- Distinguish "this change introduces no new risk" from "this code is now safe" — pre-existing risks the diff doesn't touch should be named, not implied away.
