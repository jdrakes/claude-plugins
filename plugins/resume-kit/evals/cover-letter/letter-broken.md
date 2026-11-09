# Lakeside Freight, Staff Backend Engineer

- Drafted: 2026-01-20, against the live resume
- Posting: https://example.com/lakeside-freight/careers/staff-backend-engineer (saved as `posting.txt`)
- Team: Shipment Platform
- Location: Remote (United States)
- Compensation: $190,000 to $225,000 base
- Base used: `2026-01-12-base-backend-engineer-cover-letter.md`. Every stated
  requirement is backend or data-service work, which is when that base
  applies. Its paragraph order stands: the posting screens first for a
  migration where callers moved without a coordinated release, and the
  base opens on one.

## Letter

Dear Lakeside Freight hiring team,

I am applying for the Staff Backend Engineer role. At Northwind Systems I
split the table that took every write in the company into four services, and none of its
seventeen callers had to release on the same day to make that happen. I
have spent nine years on data-heavy backend services, mostly on schemas,
queues and the paths that have to stay correct when a dependency is slow.
The parts of a system that are hard to change later are the parts I like
working on.

The split worked because of a read-only compatibility view. It kept the old
table's name and columns and joined across the four new services, so each
team moved when its own release allowed, over about five months, and the
view was dropped when the last caller left. Afterwards I wrote the
schema-change checklist the team now follows for every change: backfill,
dual writes, the read switch, and which of the two deploys goes first. I
also rewrote our nightly reconciliation job as a consumer of the
change-data-capture stream, which took the run from four hours to under ten
minutes and ended the overnight rota that existed only to restart it.

At Cobalt Harbor I built the billing export every finance tool read from.
A corrected invoice is reissued as a new record pointing at the one it
replaces, so history is never edited and finance can see both the
original and the correction. I added distributed tracing across six
services and used it to find a client retrying every failed write while
the server retried too, which had doubled database load since launch. I
removed the client's retry. I also took over a
search service nobody owned, halved its p99 latency by removing a
full-text scan that a filter triggered on every query, and documented it
well enough that two other engineers have since taken on-call for it.

The habit behind both jobs is the same: plan the migration before the
schema, measure before changing the hot path, and leave the next engineer
a document they can act on without me. Your posting says no carrier can be
asked to switch on the same day as every other; a compatibility view over
the shipment-tracking database is where I would start. I am applying
because I want my next migration to be one where a mistake shows up at a
loading dock, not in a report.

In 2024 I also led the incident response for a day-long outage at
Northwind Systems, coordinated the engineers across every affected team
through the night, and wrote the postmortem that changed how the whole
company rolls out database changes. That experience taught me a great deal
about how systems fail under real pressure and about how people work
together when the stakes are high. Lakeside Freight's move to event
sourcing is what made me apply: it is exactly the kind of architecture I
have wanted to work in for a long time, and I believe my background in
data-heavy services, migrations and reliability would let me contribute to
that effort from my very first week on the team.

I would welcome a conversation about the role and the systems behind it.
Could we find half an hour in the next couple of weeks?

Alex Rivera
alex.rivera@example.com
555-0142

## Rulings

1. **Rulings 1 to 4 of the base stand** (Alex, 2026-01-12). "The work I am
   proudest of" stays cut, "ended the overnight rota" stays, the
   tenant-isolation rollout stays out, and the closing asks for half an
   hour.
2. **The hook is Alex's, in Alex's words** (Alex, 2026-01-20). "I am
   applying because I want my next migration to be one where a mistake
   shows up at a loading dock, not in a report." Alex gave this reason
   when asked why Lakeside Freight, and confirmed the sentence as written.
3. **The company detail is the posting's no-same-day-switch line**
   (Alex, 2026-01-20). It is the posting's own constraint, quoted back, and
   the orders split is the evidence for it, so the paragraph claims
   nothing about Lakeside Freight the posting does not state.

## Confirm before sending

None.

## Gap against the posting

| Requirement | Evidence | Strength |
| --- | --- | --- |
| Lead the split of the shipment-tracking database, each carrier moving on its own schedule | Orders table split, seventeen callers, compatibility view | Strong |
| Correctness of invoicing data, how a corrected invoice is recorded | Billing export and its replay path; nightly reconciliation | Strong |
| APIs that stay correct when a carrier is slow, retries or goes down | Client and server retry loop found by tracing; per-tenant rate limits | Medium: the retry fix is about one client, not an API design |
| PostgreSQL at scale: schema changes, backfills, query performance | Schema-change checklist; search p99 halved | Strong |
| Instrument services for on-call | Distributed tracing across six services | Medium |
| Mentor engineers; write design notes others can act on | Search runbook and design note; two engineers took on-call | **Weakest.** The resume names technical mentoring as a skill but `KNOWLEDGE.md` holds no mentoring fact beyond the search handover. Prepare for the question; do not claim more in the letter |

## Evidence

| Claim in the letter | Source |
| --- | --- |
| Nine years on data-heavy backend services; schemas, queues, paths that stay correct when a dependency is slow | Resume summary |
| Split the table that took every write in the company into four services; seventeen callers, none releasing on the same day | `KNOWLEDGE.md` "Northwind Systems", Orders table split; resume bullet 1 |
| The view kept the name and columns; about five months; view dropped | `KNOWLEDGE.md` "Northwind Systems", Orders table split |
| Schema-change checklist and its steps | `KNOWLEDGE.md` "Northwind Systems", Schema-change checklist |
| Reconciliation, four hours to under ten minutes, rota ended | `KNOWLEDGE.md` "Northwind Systems", Nightly reconciliation; base ruling 2 |
| Billing export; reissue without editing history | `KNOWLEDGE.md` "Cobalt Harbor", Billing export |
| Tracing across six services; retry loop doubling database load; client retry removed | `KNOWLEDGE.md` "Cobalt Harbor", Tracing |
| Search service: unowned, p99 halved, full-text scan, two engineers | `KNOWLEDGE.md` "Cobalt Harbor", Search service |
| No carrier can be asked to switch on the same day as every other | `posting.txt`, "About the role" |
| The hook | Ruling 2 |

Not used on purpose:

- **Per-tenant rate limits**: the nearest fit for the slow-carrier
  requirement, but a third Northwind item would crowd out Cobalt Harbor.
  It is in the gap table instead.
- **Tenant-isolation rollout**: in progress, so it is not counted.
- **Incident response, postmortems, managing people**: under "Not on file"
  in `KNOWLEDGE.md`.
