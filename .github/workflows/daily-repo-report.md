---
emoji: 📰
description: Daily report on recent repository activity, delivered as an issue
intent: Give maintainers a concise daily summary of the last 24 hours of repository activity
on:
  schedule: daily
  workflow_dispatch:
permissions:
  contents: read
  issues: read
  pull-requests: read
tools:
  github:
    mode: gh-proxy
    toolsets: [default]
safe-outputs:
  create-issue:
    title-prefix: "[daily-report] "
    labels: [report]
    close-older-issues: true
    expires: 7d
---

# Daily Repository Activity Report

## Task

Summarize activity in `${{ github.repository }}` over the last 24 hours (since the previous run) using `gh` commands. Cover:

- Commits pushed to the default branch (author, summary)
- Pull requests opened, merged or closed, and those awaiting review
- Issues opened, closed or commented on
- Releases and notable failed workflow runs
- Items that need maintainer attention (stale PRs, unanswered issues)

Create one issue with a short overview followed by sections for each topic above, linking to relevant items. Use `###` or lower headings, and put long lists in `<details>` blocks. Close with a link to the workflow run.

## Safe Outputs

- Use `create-issue` to publish the report (meaningful body, not placeholder text). Newer reports replace older ones.
- If there was no activity in the window, call `noop` with a short explanation.
