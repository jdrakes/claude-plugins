---
name: schedule-rules
description: "Calendar judgment from a rules file the user writes: read the live calendar before any change, propose specific interview and call windows from open time, apply contingencies written down ahead of time, and run a daily briefing and a monthly drift review. Use whenever a task touches the user's calendar, adds a recurring or one-off commitment, resolves a conflict, proposes interview or call times, or asks about their routine or work hours, even if they do not say schedule or calendar."
---

# Schedule rules

The rules file defines every schedule fact; this skill is how to reason
with them, and holds no time or cadence of its own. Source of truth, in
order: the live calendar, then the rules file, then this skill. If the
calendar disagrees with the rules file, trust the calendar and flag the
mismatch.

It needs the live calendar: a calendar connector that can read it, and
write it for any change. If the calendar cannot be read, say so and stop.

Report plainly: a short list of concrete items, no hedging, no small talk,
and say so before changing topic.

## Inputs

- **Rules file**, required. Use the file named by the user, by the skill
  that invoked this one, or by the project's `CLAUDE.md`, in that order.
  If none names one, ask once; in an unattended run, say so and stop. Read
  it in full before anything else; if it cannot be read, stop and say so.
- **Goals file**, optional, named the same way. Only the monthly drift
  review reads it.

`examples/rules.md` in this skill's directory is a filled-in rules file
for an invented person.

## What the rules file holds

Block times, cadences, calendars and conflict priority sit under any
headings the user chooses. This skill also reads these sections by name;
a section the file leaves out has no entries.

| Section | Holds |
|---|---|
| Protected blocks | Blocks never offered for interview or call times |
| Hard boundaries | Blocks never moved, that no window starts at or runs into, and where to read each one's time |
| Cancel on out of office | Blocks cancelled on a day with an out-of-office event |
| Contingencies | Each situation and the action to take, written down ahead of time |
| Minimum buffer | The least transition time between blocks |

## Before any calendar change

1. Read today's actual calendar; block times move often.
2. Merge back-to-back blocks that share a title into one.
3. Count real transition time between blocks. A transition shorter than
   the minimum buffer is a problem, not a preference. With no minimum
   buffer set, a zero-gap handoff is.

## Proposing interview and call times

Windows come from open time, in this order: the open morning, then the
open afternoon. Never a booked work meeting, never a protected block.
Propose specific windows, not blanks. Offer 2 to 3 hours a day where the
calendar allows, merging adjacent open stretches; where it cannot without
cutting a protected block, offer the largest window and say so. Never a
window that starts at or runs into a hard boundary; read its time live, as
the rules file says. Say which blocks each window would displace; the user
approves before anything is sent.

## Contingencies

Contingencies are rules written down ahead of time, in the rules file's
Contingencies section; this skill holds none. When one applies, apply its
action as written. Out of office cancels only the blocks listed under
Cancel on out of office. A situation the section does not list is flagged
for the user, not resolved by a rule made up on the spot.

## Daily briefing

Read at the start of the day, often in a hurry. Scope: today's calendar
and, where an email connector is available, urgent or unreplied email.
Flag, as a short list: conflicts, judged by the rules file's conflict
priority; transitions shorter than the minimum buffer; back-to-back blocks
that share a title.

## Monthly drift review

Compare the month against the cadences in the rules file, read fresh,
never remembered. For each recurring commitment, say what the rules expect
and what happened, both numbers. Flag transitions shorter than the minimum
buffer and back-to-back blocks that share a title. An empty stretch is not
a failure. A commitment absent with a visible cause (a break, out-of-office
days, a pause recorded in the rules file) is a decision, not drift; name
the evidence. Describe what the calendar shows; never infer illness, mood
or motivation. If a rule and the calendar disagree for a whole month, the
rule is likelier stale: say so and suggest editing the rules file.

Then, if a goals file is named, compare the month against it. For each
goal the calendar can show, say what the goal asks and what the calendar
shows. Put each mismatch to the user as a question: change the goal, or
change the calendar. Change neither. The first review of each quarter
lists every goal, and marks those the calendar cannot show for the user to
answer. If the goals file is named but cannot be read, say so; do not skip
it silently. With no goals file named, say the goals comparison was
skipped.
