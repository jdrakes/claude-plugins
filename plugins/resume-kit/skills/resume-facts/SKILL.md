---
name: resume-facts
description: "Interviews the user about one role, card by card, and records what they say in KNOWLEDGE.md so bullets are written from facts rather than invented. Use for /resume-facts <company>, \"what should the <company> section say\", \"the current role is thin\", before any bullet is drafted for a role KNOWLEDGE.md does not cover, and whenever the screener or an assessment says a section has no mechanism or scope."
---

# resume-facts

Facts before bullets. A bullet without a fact behind it is not written;
this skill gets the fact. It writes only to `KNOWLEDGE.md`, under the
role's section, and never to a resume file. Run from the user's resume
directory: `KNOWLEDGE.md` is their file and resolves against the working
directory.

If that directory is a git checkout, check `git status -sb` and the branch
first. Read the section of `KNOWLEDGE.md` whose heading names the role's
company and dates, and ask nothing it already answers. Then interview the
user about that role through `AskUserQuestion`, one question per call, in
this order, and wait for each answer before sending the next.

Every card's question ends with this line: "Type the details in your own
words under Other: numbers, names, what you did." Options are kinds of
answer, never achievements: a kind of work (a process or system; people,
such as training, mentoring or leading; money or supplies; schedules or
logistics) or a category (measured, not measured, not sure; personal,
team, org). An option someone could pick to claim something with no fact
behind it, such as "Built a new process" or "Yes, a process", is not an
option. A number, a name, a mechanism or a date comes only from what they
type, so nothing recorded as their words is the model's. A picked option
with nothing typed records only the kind; ask for the details once, in
plain chat.

If the person answers in chat while a card is open, take that answer as
the answer to the card's question, say so in one line, and send the next
question. Never send the same card again.

1. **Scope.** Who and how many depended on the thing: teams, services,
   clients, users. What broke or stopped if it was wrong.
2. **Mechanism.** What they built or changed, on what, and what it
   replaced. The design, not the ticket. "What did you actually do" until
   the answer is a mechanism.
3. **Change.** What was different afterwards, and whether anyone measured
   it. A number only if it was measured; a measured number with its unit
   and period. "Not measured" is a complete answer and is recorded.
4. **Reach.** Whether anyone else adopted it, and who. Personal, team, or
   org; the answer decides which verb the bullet can carry.
5. **Evidence.** Where it can be checked: a repo, a document, a person, a
   review. A fact with no evidence is recorded as "not independently
   verified"; that is provenance, not a hedge. Git holds who said it and
   when.
6. **The rest.** Anything else shipped in that role with their name on it,
   one line each; "not sure" is recorded as "not sure", not chased.

Stop when each of the six has an answer or a stated "not sure". Do not ask
a seventh angle on the same fact; a fact they cannot state is not on the
resume.

## Recording

Append to that section of `KNOWLEDGE.md` (create it, headed with role,
company and dates, if none exists), one entry per fact:

```
- <the fact, in the words they used, with number, unit and period if any>.
  <Where it can be checked, or "not independently verified".>
```

A reach answer is recorded as its own line. A "not sure" is one line so
the next session does not re-ask. If the resume directory is a checkout,
commit `KNOWLEDGE.md` with a subject naming the role and a body listing
what was learned. One closing line: which facts are now available for
bullets, and which came back "not sure".

Never turn thin evidence into a documented limitation: a skill or a claim
the user states is recorded as theirs, not hedged on their behalf.
