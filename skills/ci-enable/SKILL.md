---
description: Enable CI for a repository - add GitHub Actions workflow, .gitattributes, security alerts (optionally Dependabot updates), create PR, and fix until CI passes. Use when asked to set up CI/GitHub Actions for a repository (CI入れて, ciでできるものは全部, GitHub Actions設定して).
---

## CI Enable

Set up CI (GitHub Actions) for the current repository. **Confirm with user before merging the PR.**

### Steps

#### 1. Check prerequisites

- Verify `.github/workflows/` does not already have a pull_request workflow
- If one exists, ask the user how to proceed

#### 2. Fetch template files

Download these two files:

- **Workflow**: `https://raw.githubusercontent.com/isamu/graphai_agent_template/refs/heads/main/.github/workflows/pull_request.yml`
  - Save to `.github/workflows/pull_request.yml`
- **Gitattributes**: `https://raw.githubusercontent.com/isamu/graphai_agent_template/refs/heads/main/.gitattributes`
  - Save to `.gitattributes`

If the template URLs are unreachable, generate an equivalent workflow inline (checkout, setup-node, `yarn install --frozen-lockfile`, then the lint/build/test/format steps from step 3).

#### 3. Adjust workflow steps based on package.json

Read `package.json` and check which scripts exist. Remove workflow steps that don't have a corresponding script:

| Workflow step | Required package.json script |
|---|---|
| `yarn lint` | `lint` |
| `yarn build` | `build` |
| `yarn test` | `test` (also remove if script is just `echo "Error: no test specified" && exit 1`) |
| `yarn format` | `format` |

Only keep steps that have a real corresponding script.

#### 4. Standardize lint in package.json

- Ensure the `lint` script in package.json uses `eslint` (e.g., `eslint ./src` or `eslint src`)
- The workflow will call `yarn lint`, so the script must exist and work

#### 5. Fix cross-platform issues in package.json

- Remove single quotes around glob patterns in npm scripts (Windows compatibility)
  - e.g., `prettier --write 'src/**/*.ts'` -> `prettier --write src/**/*.ts`
- Ensure glob patterns use forward slashes

#### 6. Create branch and PR

Check for a branch-name collision first: if `git rev-parse --verify ci` succeeds, use `ci-2`, `ci-3`, ... instead.

```bash
git checkout -b ci main
```

- Add files individually (NEVER `git add .`):
  ```bash
  git add .github/workflows/pull_request.yml
  git add .gitattributes
  git add package.json  # only if modified
  ```
- Commit: `chore: add CI workflow`
- Push and create PR:
  ```bash
  git push -u origin ci
  gh pr create --title "add ci" --body "$(cat <<'EOF'
  ## Summary
  - Add GitHub Actions CI workflow (lint, build, test, format)
  - Add .gitattributes for Windows line ending compatibility
  - Adjust scripts for cross-platform support
  EOF
  )"
  ```

#### 7. Fix CI until it passes

- Wait for CI to run: `gh pr checks <PR_NUMBER> --watch`
- If CI fails:
  1. Check the failure logs: `gh run view <RUN_ID> --log-failed`
  2. Fix the issue
  3. Add changed files individually and commit with descriptive message
  4. Push and repeat until CI passes
- Common fixes:
  - Missing dependencies (add with `yarn add -D`)
  - Glob quoting issues on Windows (remove single quotes)
  - ESLint config issues (flat config vs legacy)
  - Format differences (run `yarn format` and commit)

#### 8. Merge the PR

After CI passes, confirm with the user, then merge with merge commit:

```bash
gh pr merge <PR_NUMBER> --merge
```

#### 9. Enable security alerts

Enable vulnerability (security) alerts:

```bash
gh api -X PUT repos/{owner}/{repo}/vulnerability-alerts
```

Check current status:
```bash
gh api repos/{owner}/{repo}/vulnerability-alerts
```

#### 10. (Optional) Enable Dependabot

Ask the user first. If they want Dependabot:

- Enable automated security fixes:
  ```bash
  gh api -X PUT repos/{owner}/{repo}/automated-security-fixes
  ```
- Create `.github/dependabot.yml` (commit via the same PR flow as above):
  ```yaml
  version: 2
  updates:
    - package-ecosystem: "npm"
      directory: "/"
      schedule:
        interval: "weekly"
  ```

### Important Rules

- NEVER use `git add .` or `git add -A`
- NEVER use `git push --force`
- Always use `--merge` (not squash) when merging
- Confirm with user before merging
- Base the `ci` branch on `main`
