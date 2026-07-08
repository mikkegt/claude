---
description: Port a workflow, config, or tooling setup from a sibling local repo into the current one, adapting repo-specific bits. Use when the user says "../<repo>/<file> をこのレポジトリでも動くようにしたい", "../<repo>を参考にして", "〇〇と同じCIをここにも", or points at another local checkout as the reference. For npm-package version propagation across the MulmoCast ecosystem use propagate instead.
---

# Adopt From Sibling

Copy a proven setup from a neighboring local repo and adapt it here.

## Steps

1. **Read the source** file(s) in the sibling repo fully. Identify the
   repo-specific parts: secrets names, package names, paths, node versions,
   branch names, org/repo slugs.
2. **Diff the stacks.** Compare the target repo's package manager
   (yarn vs npm), TS config, scripts, and directory layout against the
   source repo's assumptions. List every adaptation needed before editing.
3. **Adapt and write** into the current repo:
   - GitHub Actions workflows: check required secrets exist
     (`gh secret list`); flag missing ones with setup instructions
     instead of silently shipping a workflow that will fail
   - package.json tooling: `yarn add -D` the missing devDependencies,
     port the scripts; propose the full delta and ask which to include
     (「開発系のツールで必要なもの、さらにある？」→ show a comparison table)
   - Repo scaffolds/templates: strip content specific to the source
     (participants, data) down to the template shape
4. **Verify it works**: workflows → trigger or `gh workflow run` /
   push to a feature branch and watch the run; scripts → run them locally.
5. Feature branch + PR as usual; note the source repo in the PR body.

## Rules

- Never copy secrets or tokens; only reference secret NAMES.
- If the source and target might drift later, note in the PR that this
  was adopted from `<source-repo>` at that point in time.
