---
name: purchase-research
description: A repeatable method for researching and deciding on a purchase (products, appliances, tech, subscriptions, or any buy with more than one option), with each decision logged to one file. Use whenever the user is comparing products or brands, weighing options before buying, asking which of two things is better, or working through a shopping decision, even if they never ask for a method by name. Do not use for a one-off factual lookup, such as the price of one item, where no comparison or decision is happening.
---

# Purchase research

The shape of the conversation, not a script; skip a step already covered.

## Input: the log directory

Decisions are logged to one directory. Use the one named by the user, by
the skill that invoked this one, or by the project's `CLAUDE.md`, in that
order. If none names one, ask once, before writing the first file; never
choose one silently. Below, `<log>` is that directory.

## The method

1. Start broad: brand against brand, or category against category, before
   comparing models.
2. Name the real constraint driving the purchase (cost of ownership, space,
   noise, a pain point) before any models are compared; it reframes every
   comparison.
3. Use real numbers: current prices, replacement cycles, and total cost over
   1 and 3 years, not sticker price.
4. Map the options to the buyer's situation: room sizes, quantities, what
   they already own.
5. Settle close calls model by model: say what the pricier option actually
   gives for the difference.
6. A constraint that surfaces later reshapes earlier picks; revisit them and
   say which changed.
7. Sequence a multi-item buy by impact and buy it in stages; after each
   purchase, restate what is left.
8. When the picks converge on one brand or option, say whether
   consolidating on it is worth it.
9. Log the decision to `<log>`, one file per decision, named from the item
   (`Air purifier: Office` becomes `air-purifier-office.md`). Create it at
   the first real constraint and reuse it after that. If `<log>` is inside
   a git repository (`git -C <log> rev-parse --is-inside-work-tree` prints
   `true`), commit each change to the file there with the reasoning in the
   commit message. If it is not, write the file and do not commit.

## The log file

```markdown
---
decided: YYYY-MM-DD      # when the pick was made
bought: YYYY-MM-DD       # when it was bought
reassess: YYYY-MM-DD     # the next replacement or maintenance point
hold: <reason>           # only while deliberately paused
---
# <Category>: <specific item or location>

**Constraint.** The real thing driving the purchase (step 2).
**Decision.** <Option>, $<price>. Runner-up: <option>, why it lost.

## Options
| Option | Price | 3-year cost | Ruled out because |
|---|---|---|---|

## Reasoning
Why the winner won, in terms of the constraint.

## Items
- [x] <item>, $<price>, bought YYYY-MM-DD
- [ ] <item>, decided: <option>, $<price>
```

`## Items` is for multi-item buys only. A frontmatter field with no value is
omitted, never written as `null`. Status is read from which fields are
present:

| Fields present | Status |
|---|---|
| `hold` | paused |
| no `decided` | deciding |
| `decided`, no `bought` | decided |
| `bought` | done |

`reassess` marks the next replacement or maintenance point, whatever the
status.

Run from `<log>`:

- Open: `grep -L "^bought:" *.md`
- Paused: `grep -l "^hold:" *.md`
- Due: `grep "^reassess:" *.md`, compared against today
- History, in a git repository: `git log -p -- <file>`

`examples/standing-desk-home-office.md` is a filled-in entry.

## Throughout

Use tables for decisions with more than one option. Keep a running tally of
decided against open, so "what's left" has a direct answer.
