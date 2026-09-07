---
description: Upgrade one or a few npm packages safely with breaking-change research and code migration. Use when the user pastes yarn upgrade-interactive rows ("name 2.1.4 ❯ 3.1.4"), names a package to bump ("あげたいけどbreaking changeある？", "安全にupdateできる？", "changelogを確認して"), especially major-version bumps. For bulk minor/patch updates + audit, use yarn-update instead.
---

# Safe Dependency Upgrade

Research-first upgrade of specific packages, with migration and runtime verification.

## Steps

1. **Parse the request**: package name(s) + current → target version
   (accept pasted `yarn upgrade-interactive` rows). Classify each as
   major / minor / patch.
2. **Check usage first.** Grep the codebase for actual imports/usages.
   If a package is unused, propose REMOVAL instead of upgrade
   (`yarn remove <pkg>`) and stop there for that package.
3. **Research breaking changes** (major bumps, or minors with a reputation):
   - Fetch the changelog / GitHub releases / migration guide for the
     TARGET version — verify API signatures against the target, never
     assume old APIs still work (global rule)
   - List each breaking change with whether this codebase is affected
4. **Known migration recipes** (verify against current docs before applying):
   `@vueuse/head` → `unhead`, pinia 2→3, vue-router 4→5, ESLint 9 flat
   config, vue-cli → vite, TS deprecations (`moduleResolution: node10`, `baseUrl`).
5. **Apply**: `yarn add <pkg>@<version>` (never edit package.json by hand),
   migrate affected code, no `as` casts / no `eslint-disable` to silence errors —
   fix types properly.
6. **Verify**:
   - `yarn format && yarn lint && yarn build` (+ `yarn typecheck` if defined)
   - Run tests
   - **Launch the dev server / drive the app** — vite optimizer and runtime
     errors do not show at build time. Use the `run` skill.
7. **PR**: unique feature branch, and include the investigation results in
   the PR body (「この調査結果もいっしょに」): breaking changes found,
   affected/not-affected judgment, migration applied.
8. Hand off to CI watching (ci-fix skill) and bot-review triage (gh-review-loop).
