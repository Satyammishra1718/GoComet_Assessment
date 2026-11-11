# Design

## Fact model

Right now the state is one file, `docs.json`: for every email and attachment, its doc path
(`batch_01/0001.eml#MSA-X.pdf`), the received date from the email's Date header, and the text of each page as
`grader/extract.py` reads it. Facts are derived at report time, so every finding can quote the exact line and page.
The plan was to add a second layer of extracted facts (invoice lines, rate tables, Schedule 1 contacts, waivers),
each pointing back to its doc, page and line.

## Conflicts

Not implemented. The idea: compare the correct amount from each source in force on the pickup date, use the
precedence rules from the glossary when they rank the sources, and escalate only when they don't.

## Confidence

Fixed at 0.9 for expiry findings, since they come straight from a signed MSA clause. A real version would lower it
for weaker sources, missing documents and uncertain extraction.

## People in the loop

The only action this version produces is `internal:alert`, which is internal, so nothing goes outbound in either
mode.

## Feedback

Feedback files are stored in the state dir but not applied yet.

## New documents

Each batch adds to `docs.json`; the report is rebuilt from all documents received by `as_of`. Amendments and
extensions are not handled yet.

## Cost

Zero model cost: this version makes no API calls. Ingesting the practice mailbox takes a few seconds.

## What I'd do next

Use an LLM to extract structured facts from invoices and contracts, then add overcharge and duplicate detection
with plain-Python arithmetic, then late-fee risk, then feedback handling and my own eval cases.
