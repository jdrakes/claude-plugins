# starter evals

Checks that a fresh folder made by the starter step passes resume-review's
first pass on the example content, end to end, and is left as it was made.

## How to run

`<P>` is the plugin directory and `<F>` the fresh folder, both absolute.

1. Disable the installed resume-kit, so the copy at `<P>` is the only one
   Claude Code can load. Note first whether `settings.json` is clean, and
   enable it again afterwards, even if the run fails:

   ```sh
   claude plugin disable resume-kit@<marketplace> --scope user
   # ... steps 2 to 4 ...
   claude plugin enable resume-kit@<marketplace> --scope user
   ```

2. Make the folder:

   ```sh
   F="$(mktemp -d)/alex"
   "<P>/skills/resume/bin/new-content-folder" "$F"
   ```

3. From `$F`, run:

   ```sh
   echo "Run the resume-kit:resume-review skill on resume-v1.yaml with no posting. Print the dispatch message you sent to the screener, then the screener's report verbatim, and nothing else." |
     claude -p --plugin-dir "<P>" --model opus --permission-mode default \
       --allowedTools "Read" "Glob" "Grep" "Skill" "Agent" "Bash(<P>/skills/resume/bin/build:*)"
   ```

   Two things this needs:

   - `--permission-mode default`. When the user's default mode is plan,
     `claude -p` plans instead of running the review.
   - The prompt on stdin. `--allowedTools` takes every argument after it,
     so a prompt written after it is read as one more tool name.

   If the output shows a permission denial for the build, rerun once with
   `"Bash"` in place of the narrower rule, and say so in "Last run".

4. Check the folder:

   ```sh
   ls -A "$F"
   find "$F" -name '*.pdf'
   ```

## Passes when

All four together. The verdict word is recorded, not gated: the content
is an invented example, and the check is that the review runs end to end.

- The dispatch is the four lines from `agents/screener.md`, with no
  `defaults:` or `own-rules:`.
- The report's first line states 1 page read.
- The report has a Verdict of call, maybe or no call, and at most six
  findings, each quoting the page.
- `ls -A` shows exactly `CLAUDE.md`, `KNOWLEDGE.md`, `drafts` and
  `resume-v1.yaml`, and `find` prints nothing.

## Last run

2026-11-09, opus, on the starter as it now ships: the current role ends
`Present`, and the Sample Labs bullet says what the process does instead
of naming its steps. The narrower build rule was enough; no rerun with
`"Bash"`.

| Check | Result |
| --- | --- |
| Dispatch | **pass.** Four lines: `content: <F>/resume-v1.yaml`, `pdf: <temp>/review-resume-v1.pdf`, `posting: none`, `today: 2026-11-09`. No `defaults:` or `own-rules:` |
| First line | **pass.** "I read 1 of 1 pages." |
| Verdict and findings | **pass.** Verdict maybe, six findings, five quoting a line of the page and the first naming the Employment History section as a whole |
| Folder left alone | **pass.** `ls -A` shows `CLAUDE.md`, `KNOWLEDGE.md`, `drafts`, `resume-v1.yaml`; `find` prints nothing |

The date line now reads "MAR 2022 - PRESENT", and the screener computed
both tenures from it.

The six findings, most severe first: three bullets for more than eight
years, with the main column ending past the middle of the page; the
summary's "eight years on order and billing services" not backed by the
Sample Labs bullet; the phone number "(555) 0142" is not dialable; no
technology named in any bullet; "Built the order service that 40 internal
teams call" does not say whether Alex led it; the "Portfolio" and "Source"
links hide their URLs. It also noted, from the YAML header, that the
content is an invented example.

No finding names a content rule, and none cites a rule against the
starter's own text.

The run before this one, on the same day, used the six-line dispatch the
screener had before it stopped reading the content rules, and two of its
findings named a content rule against the starter: "replacing three copies
of the same logic" (least-charitable) and "from backfill to the order of
the two deploys" (mechanism jargon). Its top finding was the current
role's date line, "MAR 2022" with no end date. All three are fixed in
what the starter now ships.
