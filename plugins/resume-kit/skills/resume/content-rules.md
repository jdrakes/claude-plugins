# Content rules

resume-kit's default rules for what a resume, a cover letter or an
application answer says. The `resume-writer` and `letter-reader` agents
and the `resume` and `cover-letter` skills read this file first, then the
`## Content rules` section of the `CLAUDE.md` in your content folder. A
rule there adds to these; where it contradicts one of these, it wins. The
`screener` reads neither, because a recruiter's cold read does not know
the writer's rules.

## Sources

- A fact goes in only when a primary source supports it: the company's own
  site, a document, a repository, or the person whose resume it is. A
  profile snippet, a search result or an inference is not a source.
- A skill the owner says they have is a skill. Do not hedge it or file it
  as a gap unless they say so.
- Work still in progress is described, not counted, in a bullet, a cover
  letter or an application answer. Finished, measured work keeps its
  figures.

## Wording

- Read every bullet about a past employer as its least charitable current
  employee would: say what was built, never that the company was deficient
  before it or that something it still runs was eliminated. A before and
  after number for the owner's own work passes ("cut the nightly run from
  four hours to twenty minutes"); a sentence describing the employer's
  system as broken or wasteful does not.
- Readable beats keywords: a phrase kept only to match a screen goes if the
  line reads worse with it.
- No on-call or maintenance clauses, and no mechanism jargon a recruiter
  cannot use when the claim itself is the point.

## Fit

- Content first, revision second, fit last. When a page does not fit,
  collapse an older, less relevant role; never delete the claim and never
  shrink the margins.

## Workflow

- Draft before live. A content change is drafted in
  `drafts/<live-name>-draft.yaml`, never in the live file. Build it and
  read the PDF, since page count and section balance are misjudged from
  YAML. Only then is it promoted, and promoting is the owner's call: it
  moves to the top level under the next version number (a draft of
  `resume-v1.yaml` becomes `resume-v2.yaml`). Nothing is overwritten or
  deleted; every version keeps its name.
- The resume and the owner's public profile, such as a professional
  networking profile or a personal site, must not contradict each other.

## Optional: settle positioning by measurement

A positioning question, such as which title to use or which role to lead
with, can be settled by measurement rather than taste. Build variants that
differ in that one thing, run `resume-kit:resume-review` several times per
variant against the same real postings, and count the findings as well as
the verdicts.
