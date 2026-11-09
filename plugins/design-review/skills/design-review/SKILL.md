---
name: design-review
description: "Applies design judgment and UX and accessibility practice to an existing UI, a component, or an in-flight build: look, spacing, type, colour. Use whenever the user asks for a design review, wants an interface to look better or feel cleaner, or is choosing between layout, type or colour options, even if they do not say design. Not for deciding whether or how to build something new, and not for a change with no markup, styles or rendered output."
---

# Design review

Works on the code and produces no document. It reads source, not a
rendered page. Nothing to add for a change with no markup, styles or
rendered output.

## Input: the taste file

Taste is one file of observations to weigh, never to enforce. Use the file
named by the user, by the skill that invoked this one, or by the project's
`CLAUDE.md`, in that order. If none names one, use
`references/default-taste.md` in this skill's directory. A named taste
file replaces the default whole; the two are never merged.

## The method

1. Find the project's stack and its tokens or theme file. Its own
   documented choices are precedent; if one looks wrong, say so and ask
   rather than replace it.
2. Read the taste file: one person's taste, from one project, to weigh
   rather than enforce.
3. Universal practice (WCAG AA contrast measured against the real colour
   pair, hierarchy, spacing, restraint) applies everywhere. Brand (palette,
   density, voice) belongs to one project; never carry one project's tokens
   into another. For example, an internal `billing-console` and a public
   `studio-site` built by the same team each keep their own palette, and
   neither borrows the other's tokens.
