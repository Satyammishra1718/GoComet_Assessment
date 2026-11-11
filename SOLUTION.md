# My solution

## How to run it

Python 3.11+ (I used 3.14 on Windows). No API key is needed for this version.

```
python -m venv .venv
.venv/Scripts/python -m pip install -r harness/requirements.txt     # .venv/bin/python on Linux/macOS
make grade        # or: python grader/run_grader.py --harness "python harness/harness.py" --data data/scenarios --key data/scenarios/answers --mode both --out report_card.json
make sheet        # or: python tools/run_mailbox.py --data data/exam --harness harness/harness.py --out out/exam_report.json --sheet answer_sheet.json
```

## What works

- `ingest` reads each email and its PDF/XLSX attachments with `grader/extract.py` (the grader's own reader, so
  quotes match) and stores the page text and the received date in `<state-dir>/docs.json`. It keeps state across
  batches and skips documents it has already stored.
- `report` respects `--as-of` (only documents received by that date count) and finds contract expiries: it reads the
  initial-term clause in each MSA and reports contracts whose end date is 0-60 days after `as_of`, with
  `internal:alert` and the clause as evidence.
- `feedback` stores the feedback file in the state dir.
- Practice report card: **9.3 / 100**. The expiry finding is right, and none of the five hard gates is triggered.

## What doesn't

This is a first version and covers only a small part of the brief:

- No overcharge, duplicate, waived-but-billed, late-fee or cashback detection yet, so the money totals are 0 and the
  exam answer sheet will not match the key.
- No LLM extraction yet; the expiry check uses a regex on the term clause, so other wordings (or auto-renewing
  contracts with a notice deadline, or extensions) are missed.
- No conflict / cannot_determine handling, no OCR for the scanned invoice.
- Feedback is stored but not applied.
- I did not write my own eval cases, so `make validate` will not pass the evals check.

## The eval case that caught a bug

I did not get to writing eval cases in this version. While testing on the exam mailbox I noticed the exam contracts
say "expires on" instead of "ending on", so I widened the term-clause pattern to cover both.
