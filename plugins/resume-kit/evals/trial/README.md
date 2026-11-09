# trial evals

One case per ticket from the laptop trial of 2026-11-09, about an
invented person, Dana Whitfield, a science teacher moving into
operations. Every person, school, camp and organisation in them is
invented. Each case runs by hand with `claude -p`; none runs in
`scripts/test.sh`.

## The fixture

The content folder every case copies, under `folder/`:

| File | What it is |
| --- | --- |
| `CLAUDE.md` | A byte-for-byte copy of `skills/resume/starter/CLAUDE.template.md`, the folder's own instructions as the starter makes them |
| `KNOWLEDGE.md` | Dana's recorded facts: the current teaching role, the summer camp role, and what is not on file |
| `resume-v1.yaml` | The live resume. Its summary is the placeholder "Summary to come." on purpose: a page a screener should not call |

## How to run a case

`<P>` is the plugin directory, absolute.

1. Disable the installed resume-kit, so the copy at `<P>` is the only one
   Claude Code can load, and enable it again afterwards, even if the run
   fails:

   ```sh
   claude plugin disable resume-kit@<marketplace> --scope user
   # ... steps 2 and 3 ...
   claude plugin enable resume-kit@<marketplace> --scope user
   ```

2. Make a fresh copy:

   ```sh
   F="$(mktemp -d)/dana"; cp -R "<P>/evals/trial/folder" "$F"; mkdir -p "$F/drafts"
   ```

3. From `$F`, pipe the case's prompt on stdin and save the output:

   ```sh
   echo "<the case's prompt>" |
     claude -p --plugin-dir "<P>" --model opus --permission-mode <the case's mode> \
       --allowedTools <the case's tools> > "$(dirname "$F")/reply.txt"
   ```

   Two things this needs:

   - `--permission-mode default`. When the user's default mode is plan,
     `claude -p` plans instead of running the case.
   - The prompt on stdin. `--allowedTools` takes every argument after it,
     so a prompt written after it is read as one more tool name.

   If a permission denial blocks a step, rerun once with `"Bash"` in
   place of the narrower `Bash(...)` rules, and say so in "Last run".

## LUM-67: the verdict follows the findings, no assumed pronouns

- **Prompt:** "Run the resume-kit:resume-review skill on resume-v1.yaml
  with no posting. Print the screener's report verbatim, and nothing
  else."
- **Mode:** `default`.
- **Tools:** `"Read" "Glob" "Grep" "Skill" "Agent" "Bash(<P>/skills/resume/bin/build:*)"`.
- **Passes when**, all of these:
  1. The Pass 1 verdict says "no call" and names the summary.
  2. `grep -n -w -i -E 'he|him|his|she|her|hers' reply.txt` finds no
     word that refers to Dana. Read each hit.
  3. The first line states 1 page read.
  4. There are at most six findings, each quoting the page, and none
     proposes a bullet.

### Last run

2026-11-09, opus, on the fixture as it now ships. The narrower build rule
was enough; no rerun with `"Bash"`.

| Check | Result |
| --- | --- |
| Verdict | **pass.** "No call. The summary is a placeholder ("Summary to come."), which ends the read by itself." |
| Pronouns | **pass.** The grep printed nothing. The report calls the candidate "Dana Whitfield" or "Dana" |
| First line | **pass.** "I read 1 of 1 pages" |
| Findings | **pass.** Six findings, each quoting the page; none proposes a bullet |

The verdict sentence, quoted in full: "No call. The summary is a
placeholder ("Summary to come."), which ends the read by itself. The
phone number can't be dialled, so a screener who wanted to call still
couldn't."

The six findings, most severe first: the placeholder summary; the phone
number "(555) 0199" has seven digits; the "SCIENCE TEACHER" title against
bullets about a spreadsheet, a budget and meetings; eleven years under
one title with three bullets; the camp date line "JUN 2017 - AUG 2022"
read as a second full-time job; "Manage the science department's $18,000
yearly supply budget" with no mechanism or outcome.
