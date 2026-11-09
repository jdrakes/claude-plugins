---
name: resume
description: "Builds and edits the user's resume. Use whenever they want to change a bullet, role, skill, summary or contact detail, produce a PDF to send, start a new resume folder, or ask anything about what their resume says, even if they do not say resume."
---

# resume

A Typst renderer for a resume. The content is a YAML file the user owns,
in the directory the session is run from; this skill ships no resume of its
own beyond one layout fixture. Styling is `template.typ` and
`components.typ`, and neither is edited to make a new resume.

Read the YAML to learn what a resume says, never the PDF: a PDF is a build
output and may be older than the content.

## Paths

Two roots, and they are not interchangeable.

- Everything this plugin ships sits under `${CLAUDE_SKILL_DIR}`:
  `${CLAUDE_SKILL_DIR}/bin/build`, `${CLAUDE_SKILL_DIR}/bin/new-content-folder` and its `starter/`,
  `${CLAUDE_SKILL_DIR}/bin/build-variant` and its `examples/variants/`,
  `template.typ`, `components.typ`, `design-spec.md`, `content-rules.md`, and
  the scripts under `${CLAUDE_SKILL_DIR}/tools`.
- Everything the user owns sits in the current working directory: the
  content YAML, `KNOWLEDGE.md`, `drafts/` and `CLAUDE.md`.

Write the variable verbatim in every command. A relative path with no root
resolves against the user's resume directory, where none of this plugin
exists.

Build:

```sh
${CLAUDE_SKILL_DIR}/bin/build <content.yaml>                     # review build
${CLAUDE_SKILL_DIR}/bin/build <content.yaml> -o "<send folder>/"  # send-ready copy
```

No rendered PDF is written into the content folder. With no `-o`, the PDF
goes to the system temp folder and the path is printed. A send-ready copy
goes to the send folder the content folder's `CLAUDE.md` names; when it
names none, ask the user once. With a trailing `/`, `-o` writes
`<name> Resume.pdf` there, from the content's `name:`, because the file
name is the first thing a recruiter sees. The builder expands a leading
`~`, then refuses, with nothing written, any `-o` inside the folder the
session runs from or inside the content file's folder; a relative `-o`
always is.

## Variants

A variant is a copy of a content file with some entries removed, such as a
public copy without a phone number. It is a YAML file in a `variants/` folder
beside the content files:

- `base:` names a content file in the folder above `variants/`.
- `omit:` maps `details`, `links`, `skills` or `hobbies` to substrings. Every
  entry in that section containing one of them is removed. Nothing is added
  or restated.
- `assert_absent:` lists strings that must not appear in the rendered PDF
  text.

```sh
${CLAUDE_SKILL_DIR}/bin/build-variant <variant.yaml>                 # review build, temp folder
${CLAUDE_SKILL_DIR}/bin/build-variant <variant.yaml> -o <out.pdf>    # PDF at the path given
```

`-o` must be a file path, not a folder. It is refused inside the content
folder, and a relative `-o` resolves against the folder the command runs
from. The build fails, writing nothing, when an `assert_absent` string
survives in the rendered text or when `pdftotext` is not installed. An
example is `${CLAUDE_SKILL_DIR}/examples/variants/public.yaml`.

## Starting a content folder

When the user has no content folder yet, create one where they say:

```sh
${CLAUDE_SKILL_DIR}/bin/new-content-folder <folder>
```

It refuses a folder that exists and is not empty. It writes
`resume-v1.yaml` (invented example content for Alex Rivera, to replace), an
empty `KNOWLEDGE.md`, an empty `drafts/`, and a `CLAUDE.md` that says where
the user's own content rules go and asks for their send folder. Then tell
the user to start Claude Code from that folder, since every skill resolves
its files against the folder it runs from.

## Agent names

The agents ship inside this plugin, so they resolve as
`resume-kit:resume-writer` and `resume-kit:screener`, not as
`resume-writer` and `screener`. Dispatching the bare names fails with
"Agent type not found".

## Writing a role's section from facts

If the resume directory is a git checkout, check `git status -sb` and the
branch. Copy the live file to `drafts/<live-name>-draft.yaml` if no draft
exists. Confirm `KNOWLEDGE.md` holds interview facts for the role, else run
`resume-facts` first. Then one `Agent` call with
`subagent_type: resume-kit:resume-writer`, carrying exactly these lines:

    draft: <absolute path to the draft YAML>
    role: <role, company, dates, as the draft's entry names them>
    facts: <the KNOWLEDGE.md section heading, or several, one per line>
    defaults: <absolute path to resume-kit's skills/resume/content-rules.md>
    own-rules: <absolute path to the content folder's CLAUDE.md, or "none">

`defaults:` is `${CLAUDE_SKILL_DIR}/content-rules.md`. `own-rules:` is the
working directory's `CLAUDE.md` when it has one, else "none".

Relay its report, build the draft to a temporary path, and run
`resume-kit:resume-review` on it. The summary is not the writer's. Read
`${CLAUDE_SKILL_DIR}/content-rules.md` and the content folder's
`## Content rules` first, since they bind the summary too; then draft two
candidates in chat, in the author's register, for the user to pick or
rewrite. Promoting a draft over the live file is the user's call and never
this skill's.

## After editing the template

`components.typ`'s `geo` dictionary holds measurements calibrated against a
real rendered reference, so a change to one value moves the whole page;
`${CLAUDE_SKILL_DIR}/design-spec.md` explains what each one is and why it
holds that number. After any edit to `template.typ` or `components.typ`,
run `${CLAUDE_SKILL_DIR}/tools/check-fidelity.sh`. It renders the shipped
example and compares that render elementwise against the committed
baseline, failing on any line whose text, page, column or
position moved (§7 of `design-spec.md`). If the move was deliberate,
rerun it with `--update` and commit the new baseline with the change.
