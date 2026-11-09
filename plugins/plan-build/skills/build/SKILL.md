---
name: build
description: "Execute an approved plan: a worktree, one fresh builder agent per task, the project's tests as the gate, one branch-end review, then the project's integration default. Use whenever the user approves a plan, says build, or says go on a plan that exists, even if they do not say build by name."
---

# Build

Runs an approved plan to the end without checking in. The user approved
the Summary; the rest is yours to decide, and the why goes in each task's
commit.

## Stops

Stop and ask only for: a destructive or irreversible action; spending; a
side effect outside the worktree, unless the project's integration default
names it; a task that would break a rule in `CLAUDE.md` or a spec the plan
names; a plan whose every path forward is a guess.

A `CLAUDE.md` conflict is a stop however obvious the fix looks. Quote the
conflicting text; do not edit the plan to remove it.

Do not ask whether to continue between tasks and do not send progress
summaries. If a later task depends on a decision, one line in that task's
Intent.

## Agent names

The agents ship inside this plugin, so they resolve as `plan-build:builder`
and `plan-build:reviewer`, not as `builder` and `reviewer`. Dispatching the
bare names fails with "Agent type not found".

## Models

A task's `Model` is `haiku`, `sonnet` or `opus`; absent means sonnet. If a
task fails its gate or the builder reports `stuck`, dispatch again, fresh,
on the next model up, with the failure appended to the task. A failed opus
task stops the build. The reviewer is always opus. A `stuck` that names a
missing permission is not retried: a permission does not cross the agent
boundary, so report it.

## Private data

On a public repository, commit messages, the branch name and the pull
request's title and body are public and permanent; rewriting history later
does not remove them. There they carry no private data: no person's
personal details, no private repository's name, no path under a home
directory, no credential, no term the project's `CLAUDE.md` names as
private, and no quote of a string a change removed. Name the class instead
("removed a former employer's name"). Pass this paragraph, verbatim, to
every builder and to the reviewer when the repository is public.

## 1. Set up

1. Read the whole plan. A task with `- [x] done` is finished. Check each
   remaining task against `CLAUDE.md` and any spec the plan names; a
   conflict stops here, before any worktree exists. After a context
   compaction, trust the checkboxes and `git log`, not memory.
2. Read the test command from the plan's Constraints.
3. On the base branch, `git status -sb`. Report anything uncommitted; it is
   the user's.
4. `git worktree add .claude/worktrees/<name> -b <name> <base>`. Every
   command from here runs by absolute path inside it, and every dispatch
   gets that path. `.claude/worktrees/` must be ignored in the repo. If it
   is not, stop and say so: the flow needs that line, and committing to the
   user's repo before any work has happened is not yours to decide.
5. Run the test command once. Red stops here.
6. Run `gh repo view --json visibility -q .visibility`. `PRIVATE`,
   `INTERNAL` or no remote: Private data does not apply to this build.
   Anything else, a failed call included, means it does.

## 2. Each task, in order

1. Dispatch the `plan-build:builder` agent with: the plan's absolute path,
   the task number, the test command (or "none"), and the model. Description
   `Task N: <task name>`. Tell it the plan file is not committed, so its
   commit message must say what changed, why, and any decision it made.
   When Private data applies, include its paragraph. Wait for it.
2. Gate, run by you, not taken from the report:
   - the full test command passes; with "none", repeat the builder's named
     verification;
   - the diff adds or changes a test, or the report names the `CLAUDE.md`
     exception, or the task is prose or configuration only and the report
     names the check run on it (note this reduced gate in the report);
   - exactly one new commit since the dispatch;
   - the diff touches the task's files; extra files need an explanation.
3. Fail or `stuck`: one retry per Models. Fail again: stop and report.
4. Pass: tick the task's `- [ ] done` yourself; a builder ticking its own
   box records a pass before the gate has run. Confirm the commit message
   states what it decided and why; if not, the task fails the gate. When
   Private data applies, read the message against it; on a hit, reword it
   with `git commit --amend` while that commit is still HEAD, then read it
   again.

## 3. Close

1. Run the test command; red stops here.
2. When Private data applies, draft the pull request's title and body
   first. Dispatch the `plan-build:reviewer` agent with the plan's path, the
   base SHA and the head SHA, and when Private data applies, its paragraph,
   the branch name and the drafted title and body; description
   `Review <branch>`. A private data finding stops the build here: report
   each one's commit, file and line, or field, and its class, and wait. It
   is not a fix task, because a new commit leaves the old text in history.
   For each other finding that is a real failure, append
   `### Task N: fix <finding>` (Files, Intent, Accepts when, `Model: opus`)
   and run it through step 2 once; a fix that fails is reported, not
   retried. Other findings go in the report.
3. Read the project's `Integration default` from its `CLAUDE.md` or
   `README.md`. Say one line naming it and act:
   - `push, PR, verify, merge`: `gh pr create`, with the reviewed title
     and body when Private data applies; check
     `gh pr view --json mergeable,mergeStateStatus`, up to five times if
     `UNKNOWN`; if `CONFLICTING`, merge the base in, resolve, push,
     re-check; `gh pr merge --merge --delete-branch`; pull the base; run
     the tests.
   - `merge locally`: merge into the base; run the tests.
   - `keep the branch`: nothing further.
   - absent, `ask each time`, or anything else: offer those three and wait.
   The user can override for this branch by replying before the action
   starts.
4. After a merge: if the plan's Summary names a line on the project's
   `## Builds` checklist, tick it with the merge SHA in a one-line commit on
   the base. Then `git worktree remove .claude/worktrees/<name>` and
   `git branch -D <name>`. Otherwise leave both and name the path.
5. Report: what landed, what departed from the Summary and why, which
   integration outcome ran, what is next. Nothing else is written for the
   run.
