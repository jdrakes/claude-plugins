# claude-plugins

A marketplace of two plugins: `plan-build`, an agent workflow for planning
and building software changes, and `resume-kit`, an opinionated resume
toolkit.

## Install

```
/plugin marketplace add jdrakes/claude-plugins
/plugin install plan-build@jdrakes
/plugin install resume-kit@jdrakes
```

The old `jdrakes/claude-plan-build` URL still resolves, through GitHub's
rename redirect.

## Releasing

Each plugin's manifest pins a `version`. Claude Code only treats a plugin
as updated when that string changes, so pushing ordinary commits to `main`
never rolls anything out on its own, even with auto-update on.

To cut a release:

```
scripts/release.sh <plugin> <version>
git push origin main --follow-tags
```

`scripts/release.sh` bumps the manifest's `version`, runs `scripts/test.sh`
as the gate, then commits and tags `<plugin>-v<version>`. It refuses to run
against a dirty working tree, and it stops without pushing so the rollout
stays a deliberate second step.

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
reviewer reads every commit message, the branch name and the drafted pull
request text. A hit there stops the build before anything is pushed. On a
private repository none of this runs. Commits made outside a build are not
checked.

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

An opinionated resume toolkit: a Typst renderer with its geometry
documented, an interview skill that records facts before any bullet is
written, a cold-reader screener agent, and a snapshot test that catches
layout regressions. It ships no eval suite: these skills fire on explicit
resume requests, not on the trigger ambiguity plan-build's eval exists to
measure.

### What is in it

**`resume`** (`resume-kit:resume`) is the Typst renderer. The content is a
YAML file you own; the skill ships one layout fixture and never a resume of
its own. It reads the YAML to learn what a resume says, never the PDF,
because a PDF is a build output and may be older than the content.
Dispatches `resume-kit:resume-writer` to draft a role's section from facts
in `KNOWLEDGE.md`, then `resume-kit:resume-review` on the result.

**`resume-facts`** interviews you about one role, card by card, through
`AskUserQuestion`, and records what you say in `KNOWLEDGE.md`. It writes
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

**`resume-writer`** is the subagent `resume` dispatches to turn
`KNOWLEDGE.md` facts into bullets for one role, writing only to a draft. A
bullet that reads well but rests on no recorded fact is the thing it exists
to prevent.

**`screener`** is the read only subagent `resume-review` dispatches. It
reads a built resume the way a recruiter and a hiring manager do and
reports, ranked, what would stop it getting a screen call. It never
rewrites and never proposes a bullet.

### What your project needs to provide

Run every resume-kit skill from your resume directory; each one resolves
its working files against the directory the session is started in, not a
fixed path.

| Requirement | Why |
|---|---|
| A content YAML | The source of what the resume says; the skill never reads the PDF for this |
| `KNOWLEDGE.md` | Interview facts `resume-facts` records and `resume-writer` drafts from |
| A `drafts/` directory | Where a role's section is drafted before it replaces the live file |

A posting is optional and always supplied as a file you name: `resume-review`
reads it for its second pass, and `resume-assessment` reads one posting per
line from a market file for its gap list. Neither fetches a posting itself.

Toolchain: **typst** (the snapshot baseline in `resume` was generated on
0.15.1 and verified on 0.14.2, 0.15.0 and 0.15.1), `pdftotext` from
poppler, and `python3` with `pyyaml`.

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
