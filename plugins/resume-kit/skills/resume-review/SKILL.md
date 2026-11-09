---
name: resume-review
description: "A cold read of a resume before it is sent: builds the PDF, dispatches the screener agent, and relays what would stop it getting a screen call, first on its own and then against a named posting. Use for /resume-review, /resume-review <content.yaml>, /resume-review <content.yaml> <posting file>, \"how does this resume read\", \"would this get past a recruiter\", \"read the draft against the <company> posting\", or any request to judge a resume rather than change it."
---

# resume-review

One screener, one report in chat. This skill never edits a resume; it
decides what the screener is given and relays the report unedited.

The read runs in the `resume-kit:screener` agent
(`${CLAUDE_PLUGIN_ROOT}/agents/screener.md`) because the session that
watched a bullet drafted knows what it meant and forgives the page. The
screener's standards live in that file; this skill only gathers inputs.

## 0. Where paths resolve

The working directory must be the user's resume directory. Content,
drafts and posting files resolve against it, and files this plugin ships
resolve against `${CLAUDE_PLUGIN_ROOT}`. The two roots are not
interchangeable.

This inverts a rule the skill once carried, which pinned every path to one
fixed resume directory so the question could be asked from any session.
The resume directory is now wherever the user keeps it, so the session has
to be run from there. If `KNOWLEDGE.md` is not in the working directory,
say that the session is not in a resume directory and stop. Do not guess
where the resume lives.

## 1. Resolve the inputs, do not ask

- **Content**: the file named, else the newest `*.yaml` in `drafts/`. Say
  which in the opening line. If neither exists, ask for the content file by
  name and stop; this skill does not guess which file is live.
- **PDF**: `${CLAUDE_PLUGIN_ROOT}/skills/resume/bin/build <content.yaml> -o
  /tmp/review-<stem>.pdf`, built fresh now. The screener reads the page
  because the page is what a recruiter sees; the YAML stays the source of
  what the resume says, as `resume-kit:resume` requires, and a fresh build
  cannot be stale.
- **Posting**, when one is named: the user supplies a file holding the
  posting text, and names it. Read it, never fetch it. With no posting
  file, run pass 1 only.

## 2. Dispatch

One `Agent` call, `subagent_type: resume-kit:screener`. The agent ships
inside this plugin, so the bare name `screener` fails with "Agent type not
found". The message is exactly these lines, nothing else:

    content: <absolute path to the YAML>
    pdf: <absolute path to the built PDF>
    posting: <absolute path, or "none">
    defaults: <absolute path to resume-kit's skills/resume/content-rules.md>
    own-rules: <absolute path to the content folder's CLAUDE.md, or "none">
    today: <YYYY-MM-DD>

`defaults:` is `${CLAUDE_PLUGIN_ROOT}/skills/resume/content-rules.md`.
`own-rules:` is the working directory's `CLAUDE.md` when it has one, else
"none".

## 3. Relay

Give the report back as the screener wrote it. Do not soften it, add
findings, or answer them. If it proposed a bullet or broke its ceilings,
say so in one line above the report and leave the report as is; the breach
is a finding about the agent. Then stop: no edit, no commit, no offer to
fix. A fix is a content change through `resume-kit:resume-writer` or the
author's own hand, from `KNOWLEDGE.md`.
