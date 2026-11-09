<!-- An example of a content folder's facts file. Every person, company and school in it is invented. -->

# KNOWLEDGE: Alex Rivera

The facts behind each resume bullet, in Alex's own account. A letter or a
bullet may say what is written here and nothing more. Each fact names who
gave it and when.

## Northwind Systems, Senior Software Engineer (March 2022 to Present)

- **Orders table split.** The orders table took every write in the company
  and every team read from it. Alex split it into four services: orders,
  payments, fulfilment and returns. The read-only compatibility view kept the
  old table's name and columns and joined across the four new services, so a
  caller that only read orders kept working unchanged. That is why the
  seventeen callers could migrate one at a time: each team moved when its own
  release allowed, over about five months, and no release had to be
  coordinated across teams. The view was dropped once the last caller moved.
  (Alex, 2026-01-10)
- **Nightly reconciliation.** The old job compared the whole day's orders
  against the ledger in one batch, which took four hours and needed someone
  awake to restart it when it failed. Alex rewrote it as a consumer of the
  change-data-capture stream that reconciles each change as it arrives, so the
  nightly run only checks what is left: under ten minutes. The overnight rota
  existed only for this job and was removed. (Alex, 2026-01-10)
- **Per-tenant rate limits.** One customer's bulk import used every
  connection in the pool for most of an afternoon, and every other tenant's
  requests timed out. Alex added a limit per tenant at the gateway, so one
  tenant's burst queues behind its own limit instead of everyone's.
  (Alex, 2026-01-10)
- **Schema-change checklist.** Alex wrote the checklist after the orders
  split: backfill first, then dual writes, then switch reads, then stop the
  old writes, and which of the two deploys goes first. The team uses it for
  every schema change. (Alex, 2026-01-10)

## Cobalt Harbor, Software Engineer (June 2019 to February 2022)

- **Billing export.** Every downstream finance tool read the export Alex
  built. The replay path reissues a corrected invoice as a new record that
  points at the one it replaces, so history is never edited and finance can
  see both. (Alex, 2026-01-10)
- **Tracing.** Alex added distributed tracing across six services. The
  traces showed one client retrying every failed write three times while the
  server also retried, which had doubled database load since launch. Alex
  removed the client retry, which halved database load. (Alex, 2026-01-10)
- **Search service.** Nobody owned the search service when Alex took it on.
  A filter meant to use an index ran a full-text scan on every query;
  removing it cut p99 latency by half. Alex wrote a runbook and a design note,
  and two other engineers have since taken on-call for it. (Alex, 2026-01-10)

## Pinegrove Labs, Software Engineer (August 2017 to May 2019)

- **Ingestion pipeline.** The pipeline was a set of scripts run by hand each
  morning. Alex moved it to a scheduled workflow with an alert when a run
  failed or came in late. (Alex, 2026-01-10)
- **First integration tests.** The team had unit tests only. Alex added the
  first integration suite; in its first month it caught two regressions
  before they shipped. (Alex, 2026-01-10)

## In progress

- **Tenant isolation at Northwind.** Alex is leading a rollout that moves
  each tenant's data behind its own access boundary. (Alex, 2026-01-10)

Work in progress is described, not counted.

## Not on file

Alex has said these are not true, so no letter or bullet claims them:

- Has not led an incident response.
- Has not written a postmortem.
- Has not managed people.
