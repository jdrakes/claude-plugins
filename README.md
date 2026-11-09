# claude-plugins

A marketplace of six plugins: `plan-build`, an agent workflow for
planning and building software changes, `resume-kit`, an opinionated
resume toolkit, `purchase-research`, a method for researching a purchase
and logging each decision, `design-review`, design judgment for an
existing UI, `schedule-rules`, calendar judgment from a rules file you
write, and `cold-reader`, a cold read of your own writing.

## Install

```
/plugin marketplace add jdrakes/claude-plugins
/plugin install plan-build@jdrakes
/plugin install resume-kit@jdrakes
/plugin install purchase-research@jdrakes
/plugin install design-review@jdrakes
/plugin install schedule-rules@jdrakes
/plugin install cold-reader@jdrakes
```

The old `jdrakes/claude-plan-build` URL still resolves, through GitHub's
rename redirect.

## Releasing

Each plugin's manifest pins a `version`. Claude Code only treats a plugin
as updated when that string changes, so pushing ordinary commits to `main`
never rolls anything out on its own, even with auto-update on.

Set `LEAK_NEEDLES_FILE` to the path of your private needle file before
running `scripts/release.sh`. The file holds one term per line. Blank lines
and lines starting with `#` are ignored. The leak scan checks those terms
as well as the public list, so a term that must never appear in this public
repo is caught before it ships. If the variable is set but the file holds
no terms (it is empty or has only comments), the scan fails. Without the
variable the scan checks the public list only and prints a line saying the
private list was not checked.

To cut a release:

```
LEAK_NEEDLES_FILE=/path/to/leak-needles.txt scripts/release.sh <plugin> <version>
git push origin main --follow-tags
```

`scripts/release.sh` bumps the manifest's `version`, rewrites the plugin's
stamp (below), runs `scripts/test.sh` as the gate, then commits and tags
`<plugin>-v<version>`. It refuses to run against a dirty working tree, and
it stops without pushing so the rollout stays a deliberate second step.

A version must name one set of shipped files. Each plugin keeps a stamp,
`plugins/<name>/.claude-plugin/shipped.json`, holding its version and a
SHA-256 over every shipped file's path, executable bit and bytes.
`scripts/check_versions.py` (run by `scripts/test.sh`) fails when the files
change and the stamp does not, and the message names the plugin and says to
run `scripts/release.sh`. Shipped means the files git tracks under the
plugin (`git ls-files`, read from disk) except top-level `tests/`, `evals/`
and `evals2/` (they do not change how a plugin works) and the stamp.
Untracked and ignored files never count. `git ls-files` needs no history, so
a shallow clone gives the same answer; a copy without `.git` is not
supported.

## plan-build

An opinionated Claude Code plugin for planning and building software
changes: one approved plan, one fresh subagent per task, the project's
tests as the gate, and one review at the end of the branch.

### The opinions

These are the argument, and they come before the install instructions on
purpose. If you disagree with them, the plugin is not for you.

1. **One review at the end of the branch, not one per task.** (`build` 3.2)
2. **Interruption is the cost, not the safety.** No progress summaries, and
   no asking whether to continue between tasks. (`build` opening)
3. **The orchestrator runs the gate itself and never trusts the builder's
   report.** (`build` 2.2)
4. **A subagent never ticks its own checkbox.** The tick records that the
   work passed a gate the subagent has not seen. (`builder` 3)
5. **An instruction conflict is a hard stop however obvious the fix looks.**
   Quote the conflicting text; do not edit the plan to remove it.
   (`build` Stops)
6. **Escalate models on failure, do not retry the same one.** (`build`
   Models)
7. **Subagents never spawn subagents, and say stuck after two failed
   approaches.** (`builder` 5)
8. **A test that checks source text contains a string is not a test.**
   (`builder` 6)
9. **Verdict before questions, and a "no" ships no document.** A plan for
   work that should not happen invites doing it. (`plan` 1)
10. **A task with a placeholder is not a task.** (`planner`)
11. **No praise, and no summary of what the branch does.** The person has
    the plan for that. (`reviewer` 6)
12. **Instructions rot when every mistake becomes a rule.**
    (`claude-md-rules`)
13. **Work that is one or two edits is handed back, not planned.** A plan
    costs the same whether it carries one task or ten. (`plan` 1a)

### What is in it

**`plan`** turns a request into a plan you can approve, or a reasoned no.
It gives a verdict first, with a table of what the change costs, what it
fixes and what it risks, before it asks you anything. If the simplest
version that would work is one or two edits, it names the edits and hands
them back instead of writing a document. Otherwise it decides what the
document covers and dispatches `planner`, which writes it: a Summary you
read and approve, and a Tasks section only the builder reads.

**`build`** executes an approved plan without checking in. It creates a
worktree, dispatches one fresh subagent per task, runs the project's test
command itself as the gate after each one, and ticks the checkbox only when
the gate passed. A failed task is dispatched again on the next model up,
never retried on the same one. At the end of the branch it dispatches one
review, then carries out the project's stated integration default.

**`claude-md-rules`** is a gatekeeper that runs before a rule is added to
`CLAUDE.md` or `AGENTS.md`. It filters the proposed rule: is it universal,
could a deterministic tool do it instead, would the model infer it from the
codebase anyway, is it a one off patch for a single mistake, and can it
point instead of paste. It also flags a file that has grown past the point
where instructions get followed.

**`planner`** writes one plan document from an already-decided verdict and
goal. It is dispatched by `plan` only, after it has decided do it and the
work is not too small. It investigates the codebase itself and never asks
you anything.

**`builder`** is the subagent `build` dispatches per task. It reads the
plan's Constraints and its own task, nothing else; it makes exactly one
commit with the reasoning in the body; it reports in under 15 lines; and it
stops and reports rather than resolving a conflict between the task and the
project's rules.

**`reviewer`** is the read only subagent dispatched once at the end of the
branch. It gives two verdicts, whether the branch does what the Summary
says and whether it is well built, then lists findings ranked most severe
first, each with the input or state that makes it fail.

On a public repository, `build` also keeps private data out of the text
that becomes public: the builder writes commit messages that name the
class of anything private, the gate rereads each message, and the
reviewer reads every commit message, each commit's patch, the branch name
and the drafted pull request text. A hit there stops the build before
anything is pushed. On a private repository none of this runs. Work `plan`
hands back as too small for a plan carries the same rule for its commit
message, branch and pull request, but nothing checks it.

### What your project needs to provide

| Requirement | Why |
|---|---|
| A test command, named in the plan's Constraints | It is the gate after every task |
| `.claude/worktrees/` in `.gitignore` | `build` works in a worktree there, and it will not commit that line to your repo for you |
| An `Integration default` line in `CLAUDE.md` or `README.md` | It says what happens when the branch is finished |
| Optional: private terms named in `CLAUDE.md` | On a public repository they join the classes the builder, gate and reviewer keep out of public text |

The `Integration default` line must read one of `push, PR, verify, merge`,
`merge locally`, `keep the branch` or `ask each time`. If it is absent,
`build` offers the three choices and waits.

A design page is optional. Where a project keeps one, a plan derives from
the build's issue and the section of that page the issue names.

### Does it work?

Measured over three weeks and four projects. Verdict: Adopt, as an override
of the cost-per-task criterion and not a pass on it, because cost per task is
a wash and attention is what the flow fixed. [Write up](docs/evaluation.md).

| Measure | Replaced flow | This flow |
|---|---:|---:|
| Output tokens per task | 60.7k | 38k |
| Interruptions per task | 1.47 | 0.66 |
| Context tokens, always on / on invoke, all components | 840 / 61k | 405 / 5.2k |

### Does the eval work?

No, not yet. A 20 case suite ran clean and answers nothing: must-fire 5 of
10, must-not-fire 10 of 10, overall 0.767. That score is not a pass mark.
The graders score whether the `plan` skill was invoked, and since section
`1a` landed invocation is no longer the cost event: writing a document, a
branch and a review is. Checked afterwards, 7 of the 10 must-not-fire
prompts had led to real builds, so the half that scored perfectly is
mislabelled. Record: [docs/trigger-eval-attempt.md](docs/trigger-eval-attempt.md),
[evals/README.md](plugins/plan-build/evals/README.md).

### What this cost to find out

Nine runs measured by hand, then a corpus of runs across four projects, to
learn that attention is what the flow fixes and cost per task is a wash.
Section `1a` exists because of one number out of that: a run costs about
172k output tokens and 32 minutes before it builds anything, so at one task
the ceremony is 94 percent of the tokens. The eval suite cost 4.20 USD and
653 seconds to produce a result that cannot be used as a gate.

## resume-kit

An opinionated resume and cover letter toolkit: a Typst renderer with its
geometry documented, an interview skill that records facts before any bullet
is written, cold-reader agents for the resume and the letter, and a snapshot
test that catches layout regressions. It ships no trigger eval: these skills
fire on explicit requests, not on the trigger ambiguity plan-build's eval
exists to measure. `evals/cover-letter/` holds two cases for the letter
reader, run by hand.

### What is in it

**`resume`** (`resume-kit:resume`) is the Typst renderer. The content is a
YAML file you own; the skill ships one layout fixture and never a resume of
its own. It reads the YAML to learn what a resume says, never the PDF,
because a PDF is a build output and may be older than the content.
Dispatches `resume-kit:resume-writer` to draft a role's section from facts
in `KNOWLEDGE.md`, then `resume-kit:resume-review` on the result. A review
build with no `-o` goes to the temp folder; a send-ready copy goes to a folder
you name with `-o <folder>/`, as `<Name> Resume.pdf`, and an `-o` inside your
content folder is refused, so no PDF is written into it. `bin/build-variant`
builds a variant, a copy with entries removed such as a public copy without a
phone number. It checks the rendered text to prove they are gone.

**`resume-facts`** interviews you about one role, one question at a time, through
`AskUserQuestion`, with the details always typed in your own words, and records what you say in `KNOWLEDGE.md`. It writes
only to that file, never to a resume, so a bullet is written from a fact
rather than invented.

**`resume-review`** is a cold read before a resume is sent: builds the PDF,
dispatches the `resume-kit:screener` agent, and relays what would stop it
getting a screen call, first on its own and then against a posting, when
you supply one as a file. With no posting file it runs the first pass only.

**`resume-assessment`** measures a resume: page count, bullet balance, how
much is quantified, and which skills the postings you supply ask for that
the page does not name. Market text is a file you supply, one posting per
line. With no such file it reports structure and pages only, rather than
inventing a gap list.

**`cover-letter`** (`resume-kit:cover-letter`) takes a posting. It audits the
application form first, picks a base letter from
`applications/*-base-*-cover-letter.md`, or, for a first letter, drafts one
from `KNOWLEDGE.md` and asks you to approve it, drafts from `KNOWLEDGE.md` and the
live resume only, measures the draft against the base's own length,
dispatches `resume-kit:letter-reader`, and renders the `## Letter` section
alone to PDF with the resume's fonts. A review build goes to the temp
folder; the send-ready copy goes to an output folder you name with `-o`, as
`<Name> Cover Letter.pdf`. It never writes a PDF into your content folder:
it expands a leading `~` in `-o`, then refuses any `-o` that resolves
inside the folder it runs from or inside the letter's folder, so a
relative `-o` is always refused.

**`resume-writer`** is the subagent `resume` dispatches to turn
`KNOWLEDGE.md` facts into bullets for one role, writing only to a draft. A
bullet that reads well but rests on no recorded fact is the thing it exists
to prevent.

**`screener`** is the read only subagent `resume-review` dispatches. It
reads a built resume the way a recruiter and a hiring manager do and
reports, ranked, what would stop it getting a screen call. It never
rewrites and never proposes a bullet.

**`letter-reader`** is the read only subagent `cover-letter` dispatches. It
reads the letter cold as a hiring manager would, then traces every claim,
and never proposes a sentence.

**Content rules.** `skills/resume/content-rules.md` holds the default rules
for what a resume or a letter says: where a fact may come from, how a past
employer is described, what a page that does not fit gives up first, and
drafting before the live file changes. `resume-writer` and `letter-reader`
get its path in their dispatch, with your content folder's `CLAUDE.md`. The
`## Content rules` section there holds your own rules: they add to the
defaults, and yours win where they contradict one. `screener` gets neither:
it reads the page as a recruiter would, without the writer's rules.

### What your project needs to provide

Run every resume-kit skill from your resume directory; each one resolves
its working files against the directory the session is started in, not a
fixed path.

`skills/resume/bin/new-content-folder <folder>` creates a starting folder: an example content YAML, an empty `KNOWLEDGE.md`, an empty `drafts/`, and a `CLAUDE.md` for your own content rules and your send folder. It ends by naming any missing tool.

| Requirement | Why |
|---|---|
| A content YAML | The source of what the resume says; the skill never reads the PDF for this |
| `KNOWLEDGE.md` | Interview facts `resume-facts` records and `resume-writer` drafts from |
| A `drafts/` directory | Where a role's section is drafted before it replaces the live file |
| `applications/`, made by `cover-letter` | Where `cover-letter` keeps base letters, named `*-base-*-cover-letter.md`, and each application file. A first letter drafts a base from `KNOWLEDGE.md` and waits for your approval before writing either |
| An optional `variants/` folder | Each file there is a variant of a content file in the folder above; the example is `skills/resume/examples/variants/public.yaml` |
| An optional `CLAUDE.md` in the content folder | Its `## Content rules` section adds to resume-kit's default content rules and wins where it contradicts one. `cover-letter` also reads the live resume's file name, any writing-style skill to invoke and the send folder from it |

A posting is optional and always supplied as a file you name: `resume-review`
reads it for its second pass, and `resume-assessment` reads one posting per
line from a market file for its gap list. Neither fetches a posting itself.

Toolchain: **typst** (the snapshot baseline in `resume` was generated on
0.15.1 and verified on 0.14.2, 0.15.0 and 0.15.1), `pdftotext` from
poppler (required for `build-variant`, which fails without it), and `python3` with `pyyaml`. `skills/resume/bin/check-tools` reports
any of these that is missing, with a command that installs it on a
Mac, and `new-content-folder` runs it when it creates a folder.

### The renderer

`design-spec.md` documents the reasoning behind every measured geometry
value in the Typst template: column widths, font sizes and weights,
spacing, and why each one holds the number it does. It is what makes the
renderer editable rather than magic.

`tools/check-fidelity.sh` is the only check in the kit that looks at the
rendered page rather than the source. It is a **self-snapshot** generated
on typst 0.15.1, not a comparison against another renderer's golden reference:
it renders the shipped example fixture and compares that render elementwise
against a committed baseline of its own previous render, failing on any
line whose text, page, column or position moved. Run it after any edit to
`template.typ` or `components.typ`. It runs on whatever typst is installed;
when a typst release moves the geometry the check fails, and `--update`
regenerates the baseline.

Two genuine regressions caught over this check's life: a render that
silently depended on the host's installed fonts, fixed with
`--ignore-system-fonts`, and a fixture located from `$HOME` rather than from
the script's own location, which broke on any checkout elsewhere.

`tools/calibrate.py` is not the gate; `check-fidelity.sh` is. It answers a
different question, the one a new user actually has: you have a resume
whose layout you like, produced by something other than this template, and
you want to know how close this renderer gets to it. Because the two PDFs
come from different renderers, line order, line breaking and pagination all
differ for legitimate reasons, so it finds each reference line by its text
rather than by its position and reports how far it moved, in points,
alongside the reference lines it could not find a match for and the
lines in your render that have no counterpart in the reference at all. It
never fails a build: it exits 0 whenever it ran and prints a report for you
to read, not a verdict.

    python3 tools/calibrate.py reference.pdf generated.pdf

## purchase-research

A repeatable method for researching and deciding on a purchase, and a log
format that keeps one file per decision.

### The opinions

These are the argument. If you disagree with them, the plugin is not for
you.

1. **The shape of the conversation, not a script.** Skip a step already
   covered. (`purchase-research` opening)
2. **The real constraint reframes every comparison**, so it is named before
   models are compared. (`purchase-research` step 2)
3. **Total cost over 1 and 3 years**, with real prices and replacement
   cycles, not sticker price. (`purchase-research` step 3)
4. **One file per decision**, created at the first real constraint and
   reused. When the log directory is inside a git repository, each change
   is committed with the reasoning in the commit message; otherwise the
   file is written and not committed. (`purchase-research` step 9)
5. **Status is read from which frontmatter fields are present** (`hold`,
   `decided`, `bought`, `reassess`); a field with no value is omitted,
   never `null`. (`purchase-research` The log file)
6. **A running tally of decided versus open**, so "what's left" has a
   direct answer. (`purchase-research` Throughout)

### What is in it

**`purchase-research`** (`purchase-research:purchase-research`) runs the
nine-step method: start broad, name the real constraint, use real numbers
and 1- and 3-year cost, map to the buyer's situation, settle close calls,
revisit earlier picks, stage multi-item buys, say whether to consolidate,
and log the decision. It writes one markdown file per decision to the log
directory, and commits each change when that directory is inside a git
repository. `skills/purchase-research/examples/standing-desk-home-office.md`
is an invented, filled-in entry.

### What your project needs to provide

| Requirement | Why |
|---|---|
| A log directory, named by you, by your project's `CLAUDE.md`, or by a skill of your own that invokes this one | Every decision is logged there; with none named, the skill asks once before writing the first file |
| Optional: the log directory inside a git repository | Each change to a decision file is then committed with its reasoning, so `git log -p` is the decision's history |

To fix the log directory once, write a small skill of your own whose body
names the directory and invokes `purchase-research:purchase-research`.

## design-review

Design judgment for an existing UI: a skill for the session you are in and
an agent for a UI task worth handing off. Both read source, not a rendered
page.

### The opinions

These are the argument. If you disagree with them, the plugin is not for
you.

The method:

1. **The project's own tokens are precedent.** If a documented choice looks
   wrong, say so and ask rather than replace it. (`design-review` skill,
   step 1)
2. **Universal practice applies everywhere**: WCAG AA contrast measured on
   the real colour pair, hierarchy, spacing, restraint. (skill, step 3)
3. **Brand belongs to one project.** Palette, density and voice are never
   carried into another project. (skill, step 3)
4. **Taste is weighed, not enforced.** A screen can clear the bar while
   looking nothing like the project the taste came from. (skill, Input and
   step 2)

The agent:

5. **When it is open whether the ask is a review or a change, it is a
   review**, and the agent says so: an unwanted assessment costs a message,
   an unwanted edit costs a revert. (`design-review` agent, step 1)
6. **The agent never commits, never spawns a subagent, and reports under 15
   lines.** Commits happen when the user asks. (agent, steps 2 to 4)

The default taste (`skills/design-review/references/default-taste.md`),
which a taste file of your own replaces whole:

7. **Personality is carried by typography and content, not decoration**,
   somewhere between a themed look and a generic minimal one.
8. **One accent, used sparingly, never a dominant block**, with the places
   it may appear listed.
9. **Template patterns are rejected for a stated reason**, not by default.
10. **Large, offset display type and an asymmetric hero** over small
    centred text.
11. **Monospace for dates, role lines and meta labels**; system sans for
    body and headings.

### What is in it

**`design-review` skill** (`design-review:design-review`) finds the
project's stack and its tokens or theme file, reads the taste file, and
applies universal practice and per-project brand. It works on the code and
produces no document.

**`design-review` agent** (`design-review:design-review`) takes one UI task,
decides whether it is a review or a change, reads the skill through
`${CLAUDE_PLUGIN_ROOT}`, and reports under 15 lines. It edits code for a
change and never commits.

**`skills/design-review/references/default-taste.md`** is the default
taste: five observations from the reasoning behind one personal site.

### What your project needs to provide

| Requirement | Why |
|---|---|
| A visual surface in source: markup, styles or components | Both read source, not a rendered page; with none, the agent reports `stuck` and the skill has nothing to add |
| Optional: a tokens or theme file with its choices documented | Those choices are precedent; the skill asks before replacing one |
| Optional: a taste file, named by you, by a skill of your own that invokes this one, or by your project's `CLAUDE.md` | It replaces the default taste whole; either way it is weighed, never enforced |

To use your own taste for both the skill and the agent, name your taste
file in your project's `CLAUDE.md`. A small skill of your own whose body
names the taste file and invokes `design-review:design-review` covers only
the skill: a direct dispatch of the `design-review:design-review` agent
never sees it and falls back to the default taste. When you dispatch the
agent, name the taste file in the task, or wrap the agent too.

## schedule-rules

Calendar judgment from a rules file you write: a skill that reads the live
calendar before any change, proposes interview and call windows, applies
your contingencies, and runs a daily briefing and a monthly drift review.

### The opinions

These are the argument. If you disagree with them, the plugin is not for
you.

1. **The live calendar outranks the rules file.** When they disagree,
   trust the calendar and flag the mismatch. (`schedule-rules` opening)
2. **Read today's actual calendar before any change**; block times move
   often. (Before any calendar change, step 1)
3. **Merge back-to-back blocks that share a title, and count real
   transition time**: a transition shorter than your minimum buffer is
   flagged. (Before any calendar change, steps 2 and 3)
4. **Interview windows come from open time, never protected blocks.**
   Propose specific windows, 2 to 3 hours a day where the calendar allows,
   not blanks. (Proposing interview and call times)
5. **The drift review describes what the calendar shows**; it never infers
   illness, mood or motivation. (Monthly drift review)
6. **A mismatch between a goal and the calendar is a question**: change
   the goal, or change the calendar. The skill changes neither. (Monthly
   drift review)
7. **Contingencies are rules written down ahead of time**, in your rules
   file, and applied as written. (Contingencies)

### What is in it

**`schedule-rules`** (`schedule-rules:schedule-rules`) reads your rules
file in full, then works from the live calendar: before any change it
merges same-titled back-to-back blocks and checks transition time; it
proposes interview and call windows from open time; it applies your
contingencies; and it runs a daily briefing and a monthly drift review,
which compares the month against your cadences and, if you name one, your
goals file. `skills/schedule-rules/examples/rules.md` is a rules file for
an invented person, with protected blocks, hard boundaries, contingencies
and a minimum buffer.

### What your project needs to provide

| Requirement | Why |
|---|---|
| A calendar connector that can read your calendars, and write them for any change | Every rule is checked against the live calendar; without one the skill says so and stops |
| A rules file, named by you, by a skill of your own that invokes this one, or by your project's `CLAUDE.md` | It holds every schedule fact; the skill holds none. The sections the skill reads by name are listed in its "What the rules file holds" |
| Optional: a goals file, named the same way | The monthly drift review puts each goal the calendar can show against the month; with none named, that part is skipped |
| Optional: an email connector | The daily briefing adds urgent or unreplied email |

To fix the rules file and the goals file once, write a small skill of your
own whose body names both and invokes `schedule-rules:schedule-rules`.

## cold-reader

A cold read of your own writing: a skill that gathers exactly the files a
read needs, and a read-only agent that reads one chapter, one piece or a
whole book against them and reports ranked findings in chat.

### The opinions

These are the argument. If you disagree with them, the plugin is not for
you.

1. **Judge the page, not the intent.** The reader has not seen the piece
   drafted and does not know what was meant; a reader who watched the
   drafting forgives the page. (Agent, opening; skill, opening)
2. **Never rewrite, never suggest a sentence, a word or a phrasing.** A
   suggested sentence becomes the author's sentence. The reader reports
   what is wrong and where. (Agent, opening)
3. **The reader reads only the files the dispatch names.** The record's
   reasoning is withheld: you name the paths it must never see, and it
   never sees them. (Skill, Inputs and each mode's "What the reader
   gets"; agent, opening)
4. **Ceilings are hard.** Chapter: at most 9 structural findings, 3 line
   findings and then a count, 3 possible gaps. Book: at most 12 findings,
   3 on voice, 5 possible gaps. Piece: at most 5 structural, 3 line and
   then a count. (Agent, each mode)
5. **Verdict first**: keep, rework or cut, and the one thing that
   decides it; for a book, whether it is a book. (Agent, each mode's
   Verdict)
6. **Read once as a reader, then once as an editor.** Book mode reads
   every chapter once, in order, in one agent; the book is never split
   across agents. (Agent, opening; skill, Book mode)
7. **Possible gaps in the record are stated, never ruled on**: the fact
   the page invented and where it first appears. (Agent, mode: chapter
   and mode: book)
8. **Earlier chapters outrank the voice file**, and piece mode never
   reads the voice file: a piece is judged against itself, not against a
   profile of its author. (Agent, opening and mode: piece)
9. **Piece mode asks the whole-piece question first**: a poem, whether it
   earns the themes it claims; a story, whether what the opening sets up
   is paid; an essay, whether the page proves its claim. (Agent, mode:
   piece)
10. **The report is relayed unedited.** A report that breaks its shape or
    proposes a sentence is flagged above it and left as is: the breach is
    itself a finding. (Skill, Relay)

### What is in it

**`cold-reader`**, the skill (`cold-reader:cold-reader`), decides the
mode (chapter, piece or book), resolves the piece, gathers exactly the
inputs that mode allows, dispatches one agent, and relays its report.

**`cold-reader`**, the agent (`cold-reader:cold-reader`), is read-only
(Read, Grep, Glob; no shell) and asks for Opus. Its standards and its
report shapes, one per mode, live in its file.

`skills/cold-reader/examples/` is an invented book to try it on: three
chapters in `examples/chapters/` and `examples/outline.md`, with no lore.

### What your project needs to provide

| Input | Why |
|---|---|
| A chapters directory of numbered files, such as `07-the-crossing.md` | Chapter and book mode. The highest number is the latest chapter; the two before a chapter are its voice and continuity reference |
| Optional: an outline file | The beat a chapter should serve, the threads a book should pay, and gaps in the record |
| Optional: lore, a file or a directory | Facts a chapter can contradict. A directory with a `README.md` index lets chapter mode send only the pages a chapter touches |
| Optional: a running order file | Act boundaries for book mode. The reader never sees it |
| Optional: a voice file, and the sections to read | Chapter and book mode hold it lightly; earlier chapters outrank it. Piece mode never reads it |
| Optional: the paths the reader must never see | Open questions, the reasoning behind decisions, archives, other books, a draft's own notes |
| A model that holds a whole book in one context | Book mode is never split across agents |
| A shell with `wc -w` | Book mode's word count per act |

Each is named by you, by a skill of your own that invokes this one, or by
your project's `CLAUDE.md`, in that order. To fix them once, write a small
skill whose body names them and invokes `cold-reader:cold-reader`. A
direct dispatch of the agent reads only what its dispatch names, so a
wrapper skill covers the skill, not the agent.
