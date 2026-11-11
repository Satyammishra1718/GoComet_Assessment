"""Freight invoice audit harness (first version).

The grader calls exactly these three commands, in a fresh process each time:

    python harness.py ingest <batch_dir> --state-dir <dir>
    python harness.py report --as-of YYYY-MM-DD [--mode supervised|autonomous] [--state-dir <dir>] > report.json
    python harness.py feedback <feedback.json> --state-dir <dir>

What this version does:
- ingest: reads every .eml in the batch (body + PDF/XLSX attachments) with grader/extract.py and saves the text of
  every page, with the email's received date, to <state-dir>/docs.json.
- report: finds contract expiry dates in the MSAs and reports the ones inside the 60-day window.
- feedback: saves the feedback file to <state-dir>/feedback/ (not used by the report yet).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "grader"))
import extract  # noqa: E402  (the same reader the grader uses, so quotes match)

DEFAULT_STATE = ".state"
EXPIRY_WINDOW_DAYS = 60

# "2.2 Initial term. The initial term is 12 months, ending on 2034-03-20."
# "2.2 Initial term. The initial term runs for 24 months and expires on 2032-01-11."
TERM_RE = re.compile(r"initial term.*?(?:ending on|expires on|ends on)\s+(\d{4}-\d{2}-\d{2})", re.IGNORECASE)


# ---- storage ----------------------------------------------------------------------------------------------------------
def load_docs(state_dir: str) -> list[dict]:
    f = Path(state_dir) / "docs.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else []


def save_docs(state_dir: str, docs: list[dict]) -> None:
    Path(state_dir).mkdir(parents=True, exist_ok=True)
    (Path(state_dir) / "docs.json").write_text(json.dumps(docs, indent=1), encoding="utf-8")


# ---- commands ---------------------------------------------------------------------------------------------------------
def ingest(batch_dir: str, state_dir: str) -> None:
    batch = Path(batch_dir)
    docs = load_docs(state_dir)
    seen = {d["doc"] for d in docs}
    for eml in sorted(batch.glob("*.eml")):
        rel = f"{batch.name}/{eml.name}"
        data = eml.read_bytes()
        msg = extract.parse_eml(data)
        received = parsedate_to_datetime(str(msg["Date"])).date().isoformat()

        entries = [(rel, "eml", data)]
        for name, att in extract.attachments(data):
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            if ext in ("pdf", "xlsx"):
                entries.append((f"{rel}#{name}", ext, att))

        for doc, ext, raw in entries:
            if doc in seen:
                continue
            try:
                pages = extract.pages_of(raw, ext)
            except Exception as e:  # a broken attachment shouldn't stop the batch
                print(f"skipping {doc}: {e}", file=sys.stderr)
                continue
            docs.append({"doc": doc, "received": received, "pages": pages})
            seen.add(doc)
    save_docs(state_dir, docs)


def find_expiries(docs: list[dict], as_of: date) -> list[dict]:
    items = {}
    for d in docs:
        name = d["doc"].split("#")[-1]
        if "#" not in d["doc"] or not name.upper().startswith("MSA-"):
            continue
        contract_id = name[4:].rsplit(".", 1)[0]
        for page_no, text in enumerate(d["pages"], 1):
            for line in text.split("\n"):
                m = TERM_RE.search(line)
                if not m:
                    continue
                end = date.fromisoformat(m.group(1))
                days_left = (end - as_of).days
                if 0 <= days_left <= EXPIRY_WINDOW_DAYS:
                    items[contract_id] = {
                        "id": f"expiry:{contract_id}",
                        "class": "expiry",
                        "contract_id": contract_id,
                        "verdict": "finding",
                        "amount_usd": None,
                        "amount_range": None,
                        "deadline": end.isoformat(),
                        "action": "internal:alert",
                        "confidence": 0.9,
                        "evidence": [{"doc": d["doc"], "page": page_no, "quote": line.strip()}],
                        "missing_doc": None,
                        "supersedes": [],
                        "learned_at": None,
                    }
    return list(items.values())


def report(as_of: str, mode: str, state_dir: str) -> dict:
    day = date.fromisoformat(as_of)
    docs = [d for d in load_docs(state_dir) if d["received"] <= as_of]
    return {
        "as_of": as_of,
        "mode": mode,
        "findings": [],
        "portfolio": {"cashback": [], "expiry": find_expiries(docs, day), "late_fee_risk": []},
    }


def feedback(feedback_file: str, state_dir: str) -> None:
    out = Path(state_dir) / "feedback"
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy(feedback_file, out / Path(feedback_file).name)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="harness.py", description="Freight invoice audit harness")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("ingest", help="read one batch folder into the state dir")
    p.add_argument("batch_dir")
    p.add_argument("--state-dir", default=DEFAULT_STATE)
    p = sub.add_parser("report", help="print report.json for a date")
    p.add_argument("--as-of", required=True, help="YYYY-MM-DD; only documents received by then count")
    p.add_argument("--mode", choices=["supervised", "autonomous"], default="supervised")
    p.add_argument("--state-dir", default=DEFAULT_STATE)
    p = sub.add_parser("feedback", help="take in a person's decisions (feedback.json)")
    p.add_argument("feedback_file")
    p.add_argument("--state-dir", default=DEFAULT_STATE)
    a = ap.parse_args(argv)
    if a.cmd == "ingest":
        ingest(a.batch_dir, a.state_dir)
    elif a.cmd == "report":
        json.dump(report(a.as_of, a.mode, a.state_dir), sys.stdout, indent=1)
        sys.stdout.write("\n")
    else:
        feedback(a.feedback_file, a.state_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
