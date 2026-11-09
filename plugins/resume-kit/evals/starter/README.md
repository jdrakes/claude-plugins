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
- The report has a Verdict of call, maybe or pass, and at most six
  findings, each quoting the page.
- `ls -A` shows exactly `CLAUDE.md`, `KNOWLEDGE.md`, `drafts` and
  `resume-v1.yaml`, and `find` prints nothing.

## Last run

2026-11-09, opus, the plugin as of the commit that adds this file. The
narrower build rule was enough; no rerun with `"Bash"`.
That run used the six-line dispatch the screener had before it stopped
reading the content rules; the Dispatch row below records that, not the
current four lines.

| Check | Result |
| --- | --- |
| Dispatch | **pass.** Six lines: `content: <F>/resume-v1.yaml`, `pdf: <temp>/review-resume-v1.pdf`, `posting: none`, `defaults: <P>/skills/resume/content-rules.md`, `own-rules: <F>/CLAUDE.md`, `today: 2026-11-09` |
| First line | **pass.** "I read 1 page of the PDF, all of it." |
| Verdict and findings | **pass.** Verdict maybe, six findings, each quoting the page |
| Folder left alone | **pass.** `ls -A` shows `CLAUDE.md`, `KNOWLEDGE.md`, `drafts`, `resume-v1.yaml`; `find` prints nothing |

The six findings, most severe first: the current role's date line "MAR
2022" has no end date; three bullets for about eight years; no technology
named in any bullet; no measure of size beyond "40 internal teams";
"replacing three copies of the same logic"; "from backfill to the order of
the two deploys".

Two findings name a content rule:

- "replacing three copies of the same logic", under the least-charitable
  rule: it describes the employer's earlier code as duplicated, and is
  not a before and after number for the owner's own work.
- "from backfill to the order of the two deploys", under the rule against
  mechanism jargon a recruiter cannot use.

Both quote the example `resume-v1.yaml` the starter copies. The verdict is
not gated, so neither affects the pass.

The same four checks passed on an earlier run that day, against the
plugin before the least-charitable rule was clarified.
