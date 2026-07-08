---
description: Apply the house-standard GitHub branch protection to a repo via gh api. Use when the user says "force push禁止", "mainへの直接push禁止", "PR必須にして", "review必須", "self merge禁止", "ブランチ保護して" — with a repo URL or in the current repo.
---

# Repo Protect

Configure branch protection: no force-push, no direct push to the default
branch, PR + review required, admins included.

## Steps

1. **Target**: repo from argument URL or `gh repo view --json nameWithOwner`;
   default branch from `--json defaultBranchRef`.
2. **Current state**: `gh api repos/{o}/{r}/branches/{b}/protection` (404 = none)
   and `gh api repos/{o}/{r}/rulesets`. Show the user what's already set.
3. **Ask which profile** (unless specified):
   - standard: PR required, 1 review, no force-push, no deletions, admins NOT bypassing
   - +CI: also require status checks (list candidates via `gh api repos/{o}/{r}/commits/{b}/check-runs --jq '.check_runs[].name' | sort -u`)
   - +self-merge block: require review from someone other than the author
4. **Apply** — prefer rulesets (finer control), fall back to classic protection:
   ```bash
   gh api -X PUT repos/{o}/{r}/branches/{b}/protection --input - <<'JSON'
   {
     "required_pull_request_reviews": {"required_approving_review_count": 1},
     "required_status_checks": null,
     "enforce_admins": true,
     "restrictions": null,
     "allow_force_pushes": false,
     "allow_deletions": false
   }
   JSON
   ```
   (fill `required_status_checks: {"strict": true, "contexts": [...]}` for +CI)
5. **Verify** with a GET; print a checklist of what is now enforced.
6. **Flag what the API cannot do** on this plan (e.g. review-from-non-author
   enforcement limits on free plans, org-level settings) so the user can
   finish in the UI if needed.

## Rules

- Idempotent: re-running updates the existing protection, never duplicates rulesets
  (check ruleset names before creating).
- Never loosen existing protection without the user explicitly asking.
