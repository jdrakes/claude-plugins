# Base cover letter, backend engineer

- Drafted: 2026-01-12, against the live resume
- Posting: none. This is a base; bracketed slots are filled per posting and the paragraph order stays.
- Use when: the posting's stated requirements are backend or data-service work.
- Every claim in the letter traces to a `KNOWLEDGE.md` heading or a resume
  bullet; the Evidence section below names which.

## Letter

Dear [COMPANY] hiring team,

I am applying for the [ROLE] role. At Northwind Systems I split the table
that took every write in the company into four services, and none of its
seventeen callers had to release on the same day to make that happen. I have spent nine
years on data-heavy backend services, mostly on schemas, queues and the
paths that have to stay correct when a dependency is slow. The parts of a
system that are hard to change later are the parts I like working on.

The split worked because of a read-only compatibility view. It kept the old
table's name and columns and joined across the four new services, so a
caller that only read orders kept working unchanged and each team moved
when its own release allowed, over about five months, and the view was
dropped when the last caller left. Afterwards I wrote the schema-change
checklist the team now follows for every change: backfill, dual writes,
the read switch, and which of the two deploys goes first. I also rewrote
our nightly reconciliation job as a consumer of the change-data-capture
stream, so each change is reconciled as it arrives and the nightly run,
which now checks only what is left, went from four hours to under ten
minutes.

At Cobalt Harbor I built the billing export every finance tool read from.
A corrected invoice is reissued as a new record pointing at the one it
replaces, so history is never edited and finance can see both the
original and the correction. I added distributed tracing across six
services and used it to halve database load, by removing one client's
retry of failed writes and leaving retries to the server. I also took on
the search service and halved its p99 latency by changing how one query
filter uses its index.

In both jobs I left documents other engineers work from: the
schema-change checklist at Northwind, and at Cobalt Harbor the search
service's runbook and design note, which let two other engineers take a
share of the service.
[COMPANY DETAIL: one specific thing from the posting, in one or two
sentences, and how the work above meets it.] [HOOK: why Alex is applying
to this company, in Alex's words.]

I would welcome a conversation about the role and the systems behind it.
Could we find half an hour in the next couple of weeks?

Alex Rivera
alex.rivera@example.com
555-0142

## Rulings

1. **"The work I am proudest of" was cut** (Alex, 2026-01-12). The line
   ranked Alex's own work instead of describing it. The opening states the
   claim and lets the reader rank it.
2. **The reconciliation sentence says what the rewrite does** (Alex,
   2026-01-12). `KNOWLEDGE.md` also records that the old job needed
   someone awake to restart it and that this duty ended. The letter leaves
   that out: a clause about who was kept up at night spends the sentence
   on a duty roster instead of on what was built.
3. **The tenant-isolation rollout is left out** (Alex, 2026-01-12). It is in
   progress, and work in progress is described, not counted. A posting that
   asks for multi-tenant work may earn it one described sentence in the
   `[COMPANY DETAIL]` slot.
4. **The closing asks for something** (Alex, 2026-01-12). "I look forward to
   hearing from you" asks for nothing; the closing asks for half an hour.

## Evidence

| Claim in the letter | Source |
| --- | --- |
| Nine years on data-heavy backend services; schemas, queues, paths that stay correct when a dependency is slow | Resume summary: "Backend engineer with nine years on data-heavy services" and "schemas, queue semantics, and the paths that stay correct when a dependency is slow" |
| Split the table that took every write in the company into four services | `KNOWLEDGE.md` "Northwind Systems", Orders table split; resume: "Split a single write-heavy orders table into four services" |
| Seventeen callers, none releasing on the same day | Resume: "so the seventeen callers could migrate one at a time rather than in a single coordinated release" |
| The view kept the name and columns, joined across the services; a caller that only read orders kept working unchanged; about five months; view dropped | `KNOWLEDGE.md` "Northwind Systems", Orders table split |
| Schema-change checklist and its steps | `KNOWLEDGE.md` "Northwind Systems", Schema-change checklist; resume: "covering backfills, dual writes and the order the two deploys must happen in" |
| Reconciliation on the change-data-capture stream; each change reconciled as it arrives; four hours to under ten minutes | `KNOWLEDGE.md` "Northwind Systems", Nightly reconciliation; resume: "moved the run from four hours to under ten minutes" |
| Billing export every finance tool read; reissue without editing history; finance sees both | `KNOWLEDGE.md` "Cobalt Harbor", Billing export; resume: "Built the billing export used by every downstream finance tool" |
| Tracing across six services, used to halve database load | `KNOWLEDGE.md` "Cobalt Harbor", Tracing (removing the client retry halved database load); resume: "Added distributed tracing across six services" |
| Removed one client's retry of failed writes, leaving retries to the server | `KNOWLEDGE.md` "Cobalt Harbor", Tracing: the server also retried, and Alex removed the client retry |
| Took on the search service; p99 halved by changing how one query filter uses its index | `KNOWLEDGE.md` "Cobalt Harbor", Search service; resume: "cut its p99 latency by half by removing an accidental full-text scan" |
| Documents other engineers work from: the checklist the team uses; the search runbook and design note, after which two other engineers took a share of the service | `KNOWLEDGE.md` "Northwind Systems", Schema-change checklist; `KNOWLEDGE.md` "Cobalt Harbor", Search service |

Not used on purpose:

- **Tenant-isolation rollout** (`KNOWLEDGE.md` "In progress"): in progress,
  so it is not counted. See ruling 3.
- **Per-tenant rate limits**: true, but a third Northwind item would crowd
  out Cobalt Harbor, and it is the one most likely to be swapped in for a
  posting about multi-tenant platforms.
- **Pinegrove Labs**: the earliest role, and both items are smaller than the
  Northwind and Cobalt Harbor evidence.
- **Incident response, postmortems, managing people**: listed under "Not on
  file" in `KNOWLEDGE.md`. No letter claims them.
