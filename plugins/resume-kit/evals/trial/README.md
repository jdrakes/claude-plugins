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

## LUM-68: the writer keeps stated results and who did the work

- **Setup**, after "How to run" step 2:

  ```sh
  cp "<P>/evals/trial/writer-draft.yaml" "$F/drafts/resume-v1-draft.yaml"
  ```

  `writer-draft.yaml` is `folder/resume-v1.yaml` with one change: the
  Northgate entry's bullets are `bullets: []`.
- **Prompt:** "Make exactly one Agent call with `subagent_type:
  resume-kit:resume-writer` and the five lines below as its whole
  message, then print the agent's report verbatim and nothing else."
  Follow it with these lines, with `$F` and `<P>` written out:

  ```
  draft: $F/drafts/resume-v1-draft.yaml
  role: Science Teacher, Northgate Middle School, AUG 2015 to Present
  facts: Northgate Middle School, Science Teacher (August 2015 to Present)
  defaults: <P>/skills/resume/content-rules.md
  own-rules: $F/CLAUDE.md
  ```

- **Mode:** `acceptEdits`.
- **Tools:** `"Agent" "Read" "Glob" "Grep" "Edit"`.
- **Passes when.** Read the Northgate entry with
  `sed -n '/company: Northgate/,/company: Maple/p' "$F/drafts/resume-v1-draft.yaml"`.
  All of these must hold:
  1. A bullet contains "almost none".
  2. The spreadsheet bullet starts with "Set up" or "Built".
  3. `grep -i -E 'to date|ongoing|currently|still|since'` on that entry
     prints nothing.
  4. The report names a `KNOWLEDGE.md` line for every bullet.
  5. The draft still parses:
     `python3 -c 'import sys, yaml; yaml.safe_load(open(sys.argv[1]))' "$F/drafts/resume-v1-draft.yaml"`.
     Run this with a python3 that has PyYAML.

### Last run

2026-11-09, opus, with the writer's three new rules. No permission
denial; no rerun.

| Check | Result |
| --- | --- |
| Stated result | **pass.** Bullet 1 ends "late orders went from most units to almost none" |
| Who did it | **pass.** Bullet 1 starts "Set up a shared lab-supply order spreadsheet" |
| Time claims | **pass.** The grep printed nothing |
| Report traces | **pass.** Each of the four bullets names its `KNOWLEDGE.md` lines |
| Parses | **pass.** `yaml.safe_load` read the draft without error |

The Northgate bullets as written:

- Set up a shared lab-supply order spreadsheet for all six science
  teachers in fall 2020, and places the department's orders from it each
  month; late orders went from most units to almost none.
- Manages the science department's $18,000 yearly supply budget for six
  teachers.
- Runs the science department's monthly planning meetings, where the six
  teachers agree the next month's labs and the rooms they need.
- Mentored three first-year teachers, one a year from 2021 to 2023.

The report itself named a mixed tense in bullet 1 ("Set up" with
"places"). That is LUM-69's check, not this case's.

## LUM-69: basics through a draft

- **Setup**, in place of "How to run" step 2, a folder made by the
  starter, not a copy of the fixture:

  ```sh
  F="$(mktemp -d)/dana"; "<P>/skills/resume/bin/new-content-folder" "$F"
  ```

- **Prompt:** "Put my basics on my resume: my name is Dana Whitfield, I am
  a science teacher, I live in Columbus, Ohio, my email is
  dana.whitfield@example.com and my phone is (555) 0199."
- **Mode:** `acceptEdits`.
- **Tools:** `"Read" "Glob" "Grep" "Skill" "Edit" "Bash(cp:*)" "Bash(mkdir:*)"`.
- **Passes when**, all of these:
  1. `cmp "$F/resume-v1.yaml" "<P>/skills/resume/starter/resume-v1.yaml"`
     prints nothing.
  2. `drafts/resume-v1-draft.yaml` holds "Dana Whitfield" and
     "dana.whitfield@example.com".
  3. `diff <(grep -E '^[[:space:]]*#' "<P>/skills/resume/starter/resume-v1.yaml") <(grep -E '^[[:space:]]*#' "$F/drafts/resume-v1-draft.yaml")`
     prints nothing.
  4. The reply says in one line that the change is in the draft and the
     live resume changes when they promote it.

### Last run

2026-11-09, opus, with the new "Changing what the resume says" section.
No permission denial blocked a step; no rerun. The run also asked for a
review build, which the tool list does not allow, and said so.

| Check | Result |
| --- | --- |
| Live file unchanged | **pass.** `cmp` printed nothing |
| Basics in the draft | **pass.** The draft holds "Dana Whitfield" and "dana.whitfield@example.com" |
| Comments kept | **pass.** The `diff` printed nothing. The comment at the end of the `title:` line stayed too |
| One-line draft note | **pass.** "Your basics are in the draft, `drafts/resume-v1-draft.yaml`." |

The reply's draft lines, quoted: "Your basics are in the draft,
`drafts/resume-v1-draft.yaml`. Your live resume, `resume-v1.yaml`, has
not changed. It changes only when you tell me to promote the draft."

## LUM-69: the send build flags long bullets and mixed tense

- **Setup**, after "How to run" step 2:

  ```sh
  cp "<P>/evals/trial/send-resume.yaml" "$F/resume-v1.yaml"; O="$(mktemp -d)"
  ```

  `send-resume.yaml` is a finished page for Dana with two faults on
  purpose. Its first Northgate bullet renders on 4 lines, and that role
  pairs a present-tense "Run" with a past-tense "Mentored".
- **Prompt:** "Make me a PDF I can send. My send folder is `$O/`", with
  `$O` written out.
- **Mode:** `default`.
- **Tools:** `"Read" "Glob" "Grep" "Skill" "Edit" "Bash(<P>/skills/resume/bin/build:*)" "Bash(pdftotext:*)"`.
- **Passes when**, all of these:
  1. The reply quotes "Set up the shared order spreadsheet" as over 3
     lines.
  2. It names "Mentored" beside a present-tense verb from the Northgate
     role.
  3. It asks in one line whether to fix first.
  4. `find "$O" -name '*.pdf'` prints nothing.

### Last run

2026-11-09, opus, with the new "Before a send-ready build" section. No
permission denial; no rerun.

| Check | Result |
| --- | --- |
| Long bullet | **pass.** Names the Science Teacher bullet "Set up the shared order spreadsheet..." at 4 lines |
| Mixed tense | **pass.** Says "Run" (present) is next to "Mentored" (past) |
| Asks first | **pass.** "Should I fix these in a draft first, or make the PDF to send as it is now?" |
| No send copy | **pass.** `find "$O" -name '*.pdf'` printed nothing |

The reply's flag lines, quoted: "One bullet runs over 3 lines", "Present
and past tense mixed in one role". It also asked whether to save the send
folder to `CLAUDE.md`, and did not change the file before the answer.

## LUM-70: one card at a time

`claude -p` cannot show cards, so this case checks the first card's
content and the owner checks the interview by hand in the trial.

- **Prompt:** "Interview me with the resume-kit:resume-facts skill about a
  role not yet in KNOWLEDGE.md: Library Assistant, Riverside Public
  Library, September 2013 to June 2015. This session cannot show
  question cards. Instead of calling AskUserQuestion, print the exact JSON
  input you would pass to it for the first card, then stop."
- **Mode:** `default`.
- **Tools:** `"Read" "Glob" "Grep" "Skill"`.
- **Passes when**, all of these:
  1. The JSON's `questions` array has exactly one item.
  2. Its question text ends with the "Type the details in your own words
     under Other" line.
  3. No option label is a claim. A claim is a verb in the past tense with
     an object, or a label starting "Yes,".
  4. Every label is a kind of work or a category.

### Last run

2026-11-09, opus, with the new interview rules. No permission denial; no
rerun.

| Check | Result |
| --- | --- |
| One question | **pass.** The `questions` array holds 1 item |
| Details line | **pass.** The question text ends "Type the details in your own words under Other: numbers, names, what you did." |
| No claim labels | **pass.** "Patrons / public", "Staff / volunteers", "Programs / services", "Not sure" |
| Kinds only | **pass.** Three kinds of audience or service, and "Not sure" |

The first card's JSON, quoted: `{"questions": [{"question": "Library
Assistant, Riverside Public Library, September 2013 to June 2015. Scope:
who depended on your work there, and how many? ... Type the details in
your own words under Other: numbers, names, what you did.", "header":
"Scope", "multiSelect": true, "options": [{"label": "Patrons / public"},
{"label": "Staff / volunteers"}, {"label": "Programs / services"},
{"label": "Not sure"}]}]}`.

## LUM-66: a first letter creates the base

The fixture folder has no `applications/` and so no base letter. The
posting is `posting.txt`; its organisation, Columbus Youth Arts Alliance,
is invented.

- **Run 1 prompt:** "Write a cover letter for this posting:" then a blank
  line, then the contents of `<P>/evals/trial/posting.txt`:

  ```sh
  { printf 'Write a cover letter for this posting:\n\n'; cat "<P>/evals/trial/posting.txt"; } |
    claude -p --plugin-dir "<P>" --model opus --permission-mode acceptEdits \
      --allowedTools <the tools below> > "$(dirname "$F")/reply-1.txt"
  ```

- **Run 2:** from `$F`, `claude -p -c` with the same flags and this
  prompt: "Hook, in my words: I keep a department of six teachers
  supplied and on schedule, and I want to do that for twelve sites of
  arts programs. Yes, the base is approved." Save the output to
  `reply-2.txt`.
- **Mode:** `acceptEdits`.
- **Tools:** `"Read" "Glob" "Grep" "Skill" "Agent" "Write" "Edit" "Bash(mkdir:*)" "Bash(<P>/skills/cover-letter/bin/build-letter:*)"`.
- **Passes when**, all of these:
  1. `reply-1.txt` has no "can't write this letter yet" and no "cannot
     write".
  2. `reply-1.txt` asks the hook, asks approval in one line, and shows a
     drafted letter.
  3. After run 1, no `*-cover-letter.md` exists under `$F/applications`.
  4. After run 2, `$F/applications` holds one
     `*-base-*-cover-letter.md`, with an `Approved:` line and neither
     "DRAFT" nor "awaiting approval". Match "DRAFT" by case: the
     example's header line `- Drafted: <date>` is part of the shape, not
     a status.
  5. After run 2, `$F/applications` also holds one letter for Columbus
     Youth Arts Alliance. Its `## Letter` contains the hook in Dana's
     words, and it has an `## Evidence` section.
  6. `reply-2.txt` reports the cold read's result. That is the sign
     letter-reader ran.

### Last run

2026-11-09, opus, with the new "No base found" step. No permission
denial; no rerun.

| Check | Result |
| --- | --- |
| Never "cannot" | **pass.** Neither phrase is in `reply-1.txt` |
| One message | **pass.** The hook question, then "Is this your base letter? Say yes, or tell me what to change.", then the drafted `## Letter` with `[COMPANY]`, `[ROLE]`, `[COMPANY DETAIL]` and `[HOOK]` slots |
| Nothing before approval | **pass.** After run 1, `$F/applications` did not exist |
| Approved base | **pass.** `2026-11-09-base-operations-coordinator-cover-letter.md` has "- Approved: Dana Whitfield, 2026-11-09"; no "DRAFT" and no "awaiting approval" |
| The letter | **pass.** `2026-11-09-columbus-youth-arts-alliance-operations-coordinator-cover-letter.md`; its `## Letter` ends paragraph 3 with the hook word for word, and it has `## Evidence` |
| Cold read | **pass.** "Its verdict was "Maybe": the facts are concrete and match the job, but the hook says what you want rather than showing you can do it." |

The first 10 lines of `reply-1.txt`, quoted:

```
Dana, why do you want this operations role? One or two sentences in your own words.

Is this your base letter? Say yes, or tell me what to change.

## Letter

Dear [COMPANY] hiring team,

I am applying for the [ROLE] role. In fall 2020 I set up a shared spreadsheet where all six science teachers at Northgate Middle School request lab supplies, and I have placed the department's orders from it every month since. I also manage the department's supply budget of $18,000 a year.

```

Run 2 also wrote the hook to `KNOWLEDGE.md`, asked its open questions
one at a time, and asked for a send folder before a send build. Its
reply ran long, with tables of files and findings; reply length is
LUM-71's check, not this case's.
