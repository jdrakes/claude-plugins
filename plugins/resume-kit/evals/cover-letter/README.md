# cover-letter evals

Two cases for the `resume-kit:letter-reader` agent, both about the plugin's
invented example person, Alex Rivera. Every company, posting and fact in
them is made up.

## Why these exist

A skill that dispatches a reader can pass every structural check (the file
exists, the dispatch names the right agent, the eight lines are there) and
still ship a reader that misses what it is for. The cover-letter skill once
shipped on structural checks alone, and three defects survived that a
single real dispatch would have exposed. These cases are that dispatch:
one letter the reader should pass, and one it must catch.

## The cases

All paths are relative to the plugin directory.

| File | What it is |
| --- | --- |
| `evals/cover-letter/posting.txt` | An invented posting: Lakeside Freight, Staff Backend Engineer. Backend and data-service work only. It never mentions event sourcing |
| `evals/cover-letter/letter-good.md` | An application file built from `skills/cover-letter/examples/applications/2026-01-12-base-backend-engineer-cover-letter.md` for that posting. Slots filled, under the bar plus 42, the hook confirmed by Alex in `## Rulings`, `## Confirm before sending` at `None.` |
| `evals/cover-letter/letter-broken.md` | `letter-good.md` plus one added paragraph carrying two planted defects, and padding that takes the letter more than 100 words over the bar |

The two planted defects in `letter-broken.md`:

1. **An invented claim.** Alex led the incident response for a 2024 outage
   and wrote the postmortem. `skills/cover-letter/examples/KNOWLEDGE.md`
   says under `## Not on file` that Alex has done neither.
2. **An unconfirmed motivation.** Lakeside Freight's move to event sourcing
   is what made Alex apply. No posting says it and no ruling records it,
   and the confirmed hook in `## Rulings` gives a different reason.

## Expectations

| Case | Must report |
| --- | --- |
| `letter-good.md` | A Pass 1 verdict. **No** untraceable claim. No author-confirmation item for the hook the rulings already close |
| `letter-broken.md` | The length as a finding. **Both** planted claims as untraceable; the second also as author-confirmation required |

Both cases must leave settled `## Rulings` items alone. A reader that
re-asks a confirmed question fails even when its other findings are right.

Other findings are allowed. A **stance, unconfirmed** item for "the parts
I like working on" is expected in both cases, because no ruling confirms
that preference.

## How to run

From the plugin directory, with `P` set to its absolute path:

1. The bar is the first number of:

   ```sh
   "$P/skills/cover-letter/bin/build-letter" --words "$P/skills/cover-letter/examples/applications/2026-01-12-base-backend-engineer-cover-letter.md"
   ```

2. For each case `C` in `good` and `broken`, extract the letter alone and
   take its `words:` line:

   ```sh
   "$P/skills/cover-letter/bin/build-letter" --extract "$P/evals/cover-letter/letter-$C.md" > "/tmp/eval-letter-$C.txt"
   "$P/skills/cover-letter/bin/build-letter" --words "$P/evals/cover-letter/letter-$C.md"
   ```

3. For each case, run `claude -p --plugin-dir "$P" --model opus` with a
   prompt saying: make exactly one Agent call with `subagent_type:
   resume-kit:letter-reader` and the eight lines below as its whole
   message, then print the agent's report verbatim and nothing else.

   ```
   letter: /tmp/eval-letter-<C>.txt
   application: <P>/evals/cover-letter/letter-<C>.md
   posting: <P>/evals/cover-letter/posting.txt
   resume: <P>/skills/resume/examples/sample-resume.yaml
   knowledge: <P>/skills/cover-letter/examples/KNOWLEDGE.md
   bar: <bar>, from 2026-01-12-base-backend-engineer-cover-letter.md
   words: <the words line>
   today: <YYYY-MM-DD>
   ```

4. Confirm the report came from `resume-kit:letter-reader`. "Agent type not
   found" means the `--plugin-dir` load failed; stop there rather than
   dispatching another agent.
5. Check each report against its row above.

## Last run

2026-11-08, opus, bar 408 (base `2026-01-12-base-backend-engineer-cover-letter.md`).

- `letter-good.md`, 436 words: **pass.** Verdict interview; no untraceable claim; the hook not raised, closed by ruling 2; one stance item.
- `letter-broken.md`, 554 words: **pass.** Length reported as a finding, 146 over; the incident response and postmortem reported untraceable and contradicted by `## Not on file`; "Lakeside Freight's move to event sourcing" reported untraceable, and "is what made me apply" reported as author-confirmation required; the confirmed hook not raised again.

The first run that day failed the good case. It reported "and kept the
server's" as untraceable: `KNOWLEDGE.md` records only that Alex removed
the client retry. The sentence came from the base letter. The cases were
corrected to say only what `KNOWLEDGE.md` records, and both were rerun.
