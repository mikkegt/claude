---
description: Turn a rough idea into a well-structured GitHub issue — explore the code, enumerate design options, surface the decisions needed, then file with gh issue create. Use when the user dumps a half-formed feature/bug idea and says "よく考えてissueをつくって", "issueにして", "issue化して", "まずはissue". Issue only — never start implementing.
---

# Issue Draft

Think a rough idea through and file it as a GitHub issue.

## Steps

1. **Explore first.** Read the relevant code area (components, state,
   persistence, existing similar features) before writing a word.
   The issue must reflect how the code actually works today.
2. **Draft** in the user's language (Japanese if they wrote Japanese):
   - Problem statement / motivation — what's awkward or missing today
   - Current behavior (with `file:line` anchors where useful)
   - 2–4 design alternatives with trade-offs (e.g. auto-sort vs manual
     drag reorder), including a recommendation
3. **Decisions needed** — an explicit checklist of what the user must
   decide before implementation. Present this to the user BEFORE filing;
   anticipate the "で、何を決めれば良い？" question.
4. **File**: `gh issue create --title "..." --body "..."` with labels if
   the repo uses them. Return the URL.
5. **Stop.** Do not start implementing — that's a separate request
   (global workflow: issue → plan → implementation).

## Notes

- Multiple ideas in one dump → propose splitting into separate issues,
  confirm the split with the user first.
- If an existing open issue covers it, link/update that instead of duplicating
  (`gh issue list --search "..."`).
