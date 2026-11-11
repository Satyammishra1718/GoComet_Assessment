# GoComet Nova Take-Home Assessment

This repository contains my submission for the GoComet Nova take-home assignment on freight invoice auditing.
I implemented the harness in `harness/harness.py` with the three commands the grader calls: `ingest`, `report` and `feedback`.
The `ingest` command reads every email in a batch along with its PDF and Excel attachments.
It extracts the text page by page and saves it with each email's received date in the state folder, so data carries over between batches.
The `report` command uses only documents received on or before the given date and produces the report in the required JSON format.
It reads the term clause of each contract and raises an internal alert for contracts ending within the next 60 days, citing the clause as evidence.
The `feedback` command stores the reviewer's decisions in the state folder.
Details on running the code, the design and AI usage are in SOLUTION.md, DESIGN.md and AI_USE.md.
