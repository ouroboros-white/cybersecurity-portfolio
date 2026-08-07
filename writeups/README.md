# Write-ups

Short, structured accounts of challenges I solved myself. The point of this
folder is to show *reasoning*, which a completion count cannot: what I was
faced with, what I tried, what failed, what worked, and the underlying security
lesson.

## The bar

- **Only rooms I actually worked out.** Guided walkthrough rooms belong in
  [TRAINING.md](../TRAINING.md) as completions, not here. If the room handed me
  the answer, there is nothing to write up.
- **Reasoning, not a command log.** The failed attempts and the "why" matter
  more than the exact commands.
- **Short.** Around 200 to 350 words, four sections (below). One tight page
  beats three rambling ones.

## The shape

Every write-up follows [TEMPLATE.md](TEMPLATE.md):

1. **The target** - what I was up against, in a sentence or two.
2. **What I tried** - including the dead ends.
3. **What worked** - the step that cracked it, and why it worked.
4. **Finding & fix** - the real vulnerability in a line, and how I would defend
   against it.

## Rules I follow

- **No flags.** Never paste a room's flag or answer. The safety check blocks
  curly-brace flag patterns anyway.
- **Check the event first.** For live events with prizes, I confirm solution
  write-ups are allowed before publishing. If unsure, I draft now and publish
  after the event.
- **No em dashes.** Anywhere in this repo, including reports and commit
  messages. Heavy em dash use is one of the clearest tells of machine-written
  prose, and a reader who reads the writing as generated discounts the
  reasoning in it. Recast the sentence rather than swapping the character; a
  comma, colon, semicolon, brackets or a full stop is always available, and the
  result usually reads tighter. Check before committing:

  ```bash
  grep -rn '—' --include='*.md' .
  ```
