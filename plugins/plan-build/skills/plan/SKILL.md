---
name: plan
description: "Turn a request into a plan the user can approve, or a reasoned no. Use before any change that touches more than one file or more than one step, for any 'should we', and whenever the user says plan, even if they did not ask for a plan by name."
---

# Plan

One document, one approval. The user reads the Summary; the builder
reads the Tasks. Nothing is built here.

## 1. Verdict first

Before any question: **do it**, **do not**, or **not yet**, with a table:

| What it costs | What it fixes | What it breaks or risks |

Costs and fixes come from what was read, not guesses. A **do not** or
**not yet** ends with one sentence on what would change the answer, and
no document: a plan for work that should not happen invites doing it.

## 1a. Too small for a plan

Before writing anything, say what the simplest version that would work is.
If that is one or two edits, stop and hand it back: name the edits and say
it is too small for a plan. The session makes them. Nothing is built here,
and that includes small things. The hand-back also says that the commit
message, and any branch name or pull request text, names the class of
anything private, including what the edits remove, never the text; the
classes are in the Private data section of `../build/SKILL.md`.

A document, a fresh builder and a branch-end review cost the same whether
they carry one task or ten.

Measured over 44 runs of this flow: a run costs about 172k output tokens
and 32 minutes before it builds anything, plus about 11k and 8 minutes per
task. At one task that fixed cost is 94 percent of the tokens and 80
percent of the time.

This is the same rule as the one above, pointed the other way. A "do not"
ships no document because a plan for work that should not happen invites
doing it. A "do it" that comes to one or two edits ships no document
because the document costs more than the work.

## 2. A plan or a design

- **A plan** drives one build. Where the project keeps a design page, the
  plan derives from the build's issue and the section of that page the
  issue names, and a plan that needs the design to change stops; the page
  is edited first. Where it does not, the plan derives from the request.
- **A design**, bigger than one build, is agreed in chat the same way and
  then written into the design page: what the system is for, its parts,
  its data, its operation; nothing about how it is built. The builds it
  implies become issues in the user's tracker, one each, naming the section.
  The PR that closes the issue is the record.

## 3. Dispatch the planner

This section covers a plan; a design, above, is agreed in chat and
written into the design page, never into a document from this flow.

The document itself, its exact template and the rules for writing tasks,
is the `plan-build:planner` agent's job, not this skill's. It runs at
higher reasoning effort than a session typically carries, and it writes
the file itself. Dispatch `plan-build:planner`, not `planner`: the agent
ships inside this plugin and resolves under the plugin's namespace,
exactly as `build`'s dispatch of `plan-build:builder` does.

Compute the target path before dispatching: `plansDirectory` from
settings when the project sets one, else `~/.claude/plans/`, filed under
a slug of the title. Give the agent exactly these nine lines:

    verdict: <the decided verdict and its one-line evidence>
    goal: <what the plan is for>
    design_path: <absolute path to the file holding the design page, or "none">
    design_section: <the section within it this plan derives from, or "none">
    simplest: <the simplest version 1a named, and whether this plan is it or goes beyond it>
    untouched: <what section 1's evidence says must not change, or "none">
    path: <the computed target path>
    date: <today's date>
    repo: <absolute path to the repository this plan is for>

Wait for it. It reports `done: <path>` or `stuck: <what is missing>`. A
`stuck` is yours to resolve, not the user's, unless resolving it needs an
answer only they have. Most often that is the design page needing an edit
first, per section 2 above. Once it reports `done`, read the document
back and show the user its Summary for approval; the Tasks are the
builder's.
