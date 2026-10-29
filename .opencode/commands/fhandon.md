---
description: Focused handon — read next-fhandoff.md and carry out its one action
---

Focused handon for clothoid-lab. Work in
`/Users/thomaskelly/developer/clothoid-lab`.

1. Before any tool call, write one sentence naming the focused action you are
   about to carry out, so the operator can see you are on the right thing.
2. Read `next-fhandoff.md` at the repo root, and nothing else yet.
3. Its first line names the docs to read. Read them, in order, and stop reading
   when they tell you to.
4. Its second line is the single focused action. Do that action, and only that
   action.
5. Keep `docs/HANDOFF.md` current as you work, so a freeze costs one step and
   not the session.
6. Where a browser check is needed, drive **headless Chrome** directly with the
   DevTools Protocol (`--headless=old`, `--remote-debugging-port`). Do not look
   for a connected desktop browser, the Review pane, or Safari/safaridriver.
7. Do the action and stop. The operator runs `/fhandoff` when they want the
   focused handoff refreshed; it is not run automatically.

If `next-fhandoff.md` is missing or empty, read `docs/HANDOFF.md` and ask for the
single focused action instead of inventing one.

This is the opening command. `/fhandoff` is its twin at the other end of the
same session, but the two are not linked: `/fhandon` picks up the focused work
and stops; the operator calls `/fhandoff` to put it down and write the block
`/fhandon` will read next time.
