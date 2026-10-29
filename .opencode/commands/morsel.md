---
description: Do the next unchecked item in docs/BACKLOG.md
---

Backlog morsel for clothoid-lab. Work in
`/Users/thomaskelly/developer/clothoid-lab`.

1. Before any tool call, write one sentence naming the item you are about to do.
2. Read `docs/BACKLOG.md`. Take the first `[>]` item, otherwise the first `[ ]`
   item, and read only that item.
3. Do that item and only that item. Follow its rules. If it needs an operator
   decision, write the question under it, mark it `[~]`, and stop.
4. Run its verify command. If it fails twice for the same reason, stop and write
   the reason under the item.
5. Mark it `[x]`, update `docs/HANDOFF.md`, and commit with the item's commit
   message. Do not commit unrelated files or `out/play-template.svg`.
6. Reply with at most five bullets: item, result, commit, blocker, next item.
   Stop; do not pick up the next item.

For browser checks use headless Chrome/CDP, never the Review pane or Safari.
