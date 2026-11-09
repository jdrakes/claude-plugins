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
change-data-capture stream, so each change is reconciled as it arrives and
the nightly run, once four hours long, now checks only what is left in
under ten minutes.

At Cobalt Harbor I built the billing export every finance tool read from.
A corrected invoice is reissued as a new record pointing at the one it
replaces, so history is never edited and finance can see both the
original and the correction. I added distributed tracing across six
services, used the traces to find writes retried by both a client and the
server, and removed the client's retry so each write is retried in one
place. I also took on the search service and halved its
p99 latency by removing a full-text scan that a filter ran on every
query.

In both jobs I left documents other engineers work from: the
schema-change checklist at Northwind, and at Cobalt Harbor the search
service's runbook and design note, which let two other engineers take a
share of the service. Your posting says no carrier can be asked to switch
on the same day as every other; a compatibility view over the
shipment-tracking database is where I would start. I am applying
because I want my next migration to be one where a mistake shows up at a
loading dock, not in a report.

I would welcome a conversation about the role and the systems behind it.
Could we find half an hour in the next couple of weeks?

Alex Rivera
alex.rivera@example.com
555-0142

## Rulings

1. **Rulings 1 to 4 of the base stand** (Alex, 2026-01-12). "The work I am
   proudest of" stays cut, the reconciliation sentence says what the
   rewrite does, the tenant-isolation rollout stays out, and the closing
   asks for half an hour.
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
| Instrument services so a failure can be seen | Distributed tracing across six services | Medium |
| Mentor engineers; write design notes others can act on | Search runbook and design note; two engineers took a share of the service | **Weakest.** The resume names technical mentoring as a skill but `KNOWLEDGE.md` holds no mentoring fact beyond the search handover. Prepare for the question; do not claim more in the letter |

## Evidence

| Claim in the letter | Source |
| --- | --- |
| Nine years on data-heavy backend services; schemas, queues, paths that stay correct when a dependency is slow | Resume summary |
| Split the table that took every write in the company into four services; seventeen callers, none releasing on the same day | `KNOWLEDGE.md` "Northwind Systems", Orders table split; resume bullet 1 |
| The view kept the name and columns; about five months; view dropped | `KNOWLEDGE.md` "Northwind Systems", Orders table split |
| Schema-change checklist and its steps | `KNOWLEDGE.md` "Northwind Systems", Schema-change checklist |
| Reconciliation on the change-data-capture stream, four hours to under ten minutes | `KNOWLEDGE.md` "Northwind Systems", Nightly reconciliation; base ruling 2 |
| Billing export; reissue without editing history | `KNOWLEDGE.md` "Cobalt Harbor", Billing export |
| Tracing across six services; writes retried by both a client and the server; client retry removed | `KNOWLEDGE.md` "Cobalt Harbor", Tracing |
| Took on the search service; p99 halved by removing a full-text scan | `KNOWLEDGE.md` "Cobalt Harbor", Search service |
| Documents other engineers work from: the checklist; the search runbook and design note, two engineers taking a share of the service | `KNOWLEDGE.md` "Northwind Systems", Schema-change checklist; `KNOWLEDGE.md` "Cobalt Harbor", Search service |
| No carrier can be asked to switch on the same day as every other | `posting.txt`, "About the role" |
| The hook | Ruling 2 |

Not used on purpose:

- **Per-tenant rate limits**: the nearest fit for the slow-carrier
  requirement, but a third Northwind item would crowd out Cobalt Harbor.
  It is in the gap table instead.
- **Tenant-isolation rollout**: in progress, so it is not counted.
- **Incident response, postmortems, managing people**: under "Not on file"
  in `KNOWLEDGE.md`.
