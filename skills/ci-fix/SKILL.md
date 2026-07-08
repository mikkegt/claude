---
description: Fix a failing GitHub Actions run. Use when the user pastes an Actions run / PR URL with a failure, or says "ci失敗", "CI失敗", "CIがこけてる", "デプロイ失敗", "why did CI fail". Fetches the failing log, root-causes the FIRST real error, fixes on the PR branch, pushes, and watches the re-run until green.
---

# CI Fix

Diagnose and fix a red GitHub Actions run, then watch it back to green.

## Inputs

An Actions run URL, a PR URL/number, or nothing. With no argument, infer
from the current branch: `gh pr checks` for the branch's PR, or
`gh run list --branch <branch> --limit 5`.

## Steps

1. **Locate the failure**
   - Run URL → `gh run view <id> --log-failed`
   - PR → `gh pr checks <n>` to find the failing check, then its run id
2. **Find the FIRST real error.** CI logs cascade; the last error is
   usually a symptom. Scan for the earliest failure in the failing step.
3. **Classify** the failure:
   - lint / format / typecheck / build / test → reproduce locally
     (`yarn lint`, `yarn typecheck`, `yarn build`, `yarn test`)
   - dependency drift (lockfile, node version) → compare CI env vs local
   - deploy/permission (esp. Firebase 403 `serviceusage.serviceUsageConsumer`,
     workload-identity breakage) → this is IAM/config, not code; inspect
     roles and identity-federation settings before touching source
   - flaky/infra (network timeout, runner image) → re-run first:
     `gh run rerun <id> --failed`
4. **Root-cause before fixing** (global rule). If it's a regression,
   check `git log`/recent merges for the introducing change.
5. Never lint/fix build artifacts (`lib/`, `dist/`) — fix `src/` and rebuild.
6. Fix on the PR branch (never on main). Run the full local gate:
   `yarn format && yarn lint && yarn build`, plus `yarn typecheck` if defined.
7. Ask before committing/pushing (global rule). Commit as
   `fix: <what>`, push.
8. **Watch the re-run** in the background (`gh run watch <id>` or
   `gh pr checks <n> --watch`) and report the result. If still red,
   loop from step 1 with the new log.

## Notes

- Multiple failing checks: fix all local-gate ones in one commit, then re-check.
- If the root cause is in a different repo (shared action, published package),
  report that instead of patching symptoms here.
