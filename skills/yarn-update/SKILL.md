---
description: Update yarn dependencies with safe, staged upgrade strategy and audit. Use when asked to update/upgrade yarn dependencies or run a dependency security audit (定期アップデート).
---

## Yarn Dependency Update

### Phase 1: Safe Upgrades

Yarn 1 has no `--minor`/`--patch`/`--dev` flags for `yarn upgrade` — use npm-check-updates to edit `package.json` ranges, then `yarn install` (accepted npx exception: ncu is a one-shot tool, not a project dep).

1. **Update devDependencies (minor)**:
   ```bash
   npx npm-check-updates --dep dev --target minor -u && yarn install
   ```
2. **Update dependencies (patch)**:
   ```bash
   npx npm-check-updates --dep prod --target patch -u && yarn install
   ```
   Alternatively, use `yarn upgrade-interactive` to pick upgrades manually.
3. Run `yarn lint`, `yarn build`, `yarn test` to verify
4. Commit and create PR — wait for CI to pass before proceeding

### Phase 2: Aggressive devDependencies Upgrade

1. **Update all devDependencies to latest**:
   ```bash
   npx npm-check-updates --dep dev -u && yarn install
   ```
2. Run `yarn lint`, `yarn build`, `yarn test`
3. If issues occur, revert and report which packages caused the failure
4. If all passes, commit to the same PR

### Phase 3: Security Audit

1. **Run audit**:
   ```bash
   yarn audit
   ```
2. Yarn 1 has no `audit fix`; instead:
   - Identify the vulnerable package and its root dependency from the audit output
   - Delete ONLY the affected package's entry (and its root dependency entry) from `yarn.lock` — do NOT delete the entire file
   - Run `yarn install` to re-resolve only those packages
   - Run `yarn audit` again to verify the fix persists
   - Run `yarn lint`, `yarn build`, `yarn test` — if any fail, revert the yarn.lock change and report the vulnerability without fixing it
3. Commit fixes to the same PR. If a vulnerability cannot be fixed without breaking the build, report it to the user instead

### Phase 4: Deduplicate

Always run at the end (`npx yarn-deduplicate` is the accepted npx exception for Yarn 1 — it is a one-shot tool, not a project dep):
```bash
npx yarn-deduplicate --strategy=fewer
yarn install
```
Commit if changes were made.

### Major Bumps

This skill covers bulk minor/patch upgrades plus audit. A single-package **major** upgrade that needs breaking-change research belongs to the `dep-upgrade-safe` skill instead. If a dependency turns out to be unused, propose removing it instead of upgrading.

### Rules

- Branch name: `chore/yarn-update-YYYYMMDD` (e.g., `chore/yarn-update-20260209`) to keep names unique across runs
- Create a single PR for all phases
- Confirm CI passes after Phase 1 before proceeding to Phase 2
- If Phase 2 breaks something, revert and keep only Phase 1 changes
- Always end with deduplication
- Once CI passes, confirm with the user, then merge with `gh pr merge --merge`
