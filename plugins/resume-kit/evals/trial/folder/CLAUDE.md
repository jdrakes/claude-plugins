# Resume content

This folder holds one person's resume content: the resume YAML,
`KNOWLEDGE.md`, `drafts/` and, once you write cover letters,
`applications/`. Run Claude Code from here. How the resume looks, how it
is reviewed and the default content rules belong to the `resume-kit`
plugin; this folder holds your facts and your own rules.

## Live resume

`resume-v1.yaml` is the live resume. Change this line when a draft is
promoted to the next version.

## Content rules

resume-kit's default rules apply first: its `skills/resume/content-rules.md`.
Add your own rules below, one bullet each. A rule here adds to the
defaults, and where it contradicts one, yours wins.

## Send folder

Not set yet. Name a folder outside this one for send-ready PDFs, such as
`~/Documents/Resumes/`, and write it here in place of this paragraph.
Until it is set, Claude asks for it before a send-ready build.
