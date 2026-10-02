"""Generate the synthetic example suites in ``evals/``.

All names, addresses and numbers are fictional. Re-run with ``python scripts/generate_examples.py``;
output is deterministic for a given seed.
"""

from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "evals"

CUSTOMERS = [
    ("Harbour Lane Cafe", "Priya Shah"),
    ("Northfield Primary School", "Tom Ellery"),
    ("Greenway Care Home", "Amara Okafor"),
    ("The Copper Kettle", "Liam Doyle"),
    ("Riverside Sports Club", "Sofia Marin"),
    ("Oakbridge Office Park", "Daniel Kim"),
    ("Maple Street Deli", "Hannah Weiss"),
    ("Brightside Nursery", "Yusuf Rahman"),
]
PRODUCTS = [
    ("CUP-12OZ", "12oz paper cups (case of 1000)", 38.50),
    ("NAP-WHT", "White napkins 2-ply (case of 2000)", 21.75),
    ("GLV-NIT-M", "Nitrile gloves medium (box of 100)", 6.20),
    ("BIN-120L", "120L refuse sacks (roll of 50)", 14.99),
    ("FOIL-450", "Catering foil 450mm", 17.40),
    ("SAN-5L", "Surface sanitiser 5L", 12.30),
    ("BOX-PIZ12", "12in pizza boxes (pack of 100)", 29.95),
    ("STR-PAP", "Paper straws (box of 250)", 8.60),
    ("TRAY-ALU", "Aluminium foil trays (pack of 500)", 33.10),
    ("DET-DW5", "Dishwasher detergent 5L", 18.25),
]
STREETS = ["Mill Road", "Station Approach", "Church Lane", "Kings Avenue", "Quay Street"]
TOWNS = [("Bristol", "BS1"), ("Leeds", "LS2"), ("York", "YO1"), ("Bath", "BA1"), ("Hull", "HU1")]
DELIVERY = ["standard", "next_day", "collection"]


def _address(rng: random.Random) -> dict:
    town, prefix = rng.choice(TOWNS)
    inward = f"{rng.randint(1, 9)}{rng.choice('ABDEFGHJ')}{rng.choice('LNPQRSTUW')}"
    return {
        "line1": f"{rng.randint(1, 180)} {rng.choice(STREETS)}",
        "city": town,
        "postcode": f"{prefix} {inward}",
    }


def _date_text(d: date, rng: random.Random) -> str:
    return rng.choice(
        [
            d.strftime("%d/%m/%Y"),
            d.strftime("%-d %B %Y"),
            d.strftime("%A %-d %B %Y"),
            d.isoformat(),
        ]
    )


def order_case(i: int, rng: random.Random) -> dict:
    company, contact = rng.choice(CUSTOMERS)
    items = rng.sample(PRODUCTS, rng.randint(1, 4))
    lines = [{"sku": sku, "quantity": rng.randint(1, 12)} for sku, _, _ in items]
    delivery_date = date(2026, 3, 1) + timedelta(days=rng.randint(0, 60))
    addr = _address(rng)
    method = rng.choice(DELIVERY)
    po = f"PO-{rng.randint(10000, 99999)}" if rng.random() < 0.7 else None

    item_text = "\n".join(
        rng.choice(
            [
                f"- {ln['quantity']} x {desc} ({sku})",
                f"  {sku}  qty {ln['quantity']}",
                f"* {desc}, code {sku}, need {ln['quantity']}",
            ]
        )
        for ln, (sku, desc, _) in zip(lines, items, strict=True)
    )
    method_text = {
        "standard": "Standard delivery is fine.",
        "next_day": "We need this next day please, it's urgent.",
        "collection": "We'll collect from the depot ourselves.",
    }[method]
    po_text = f"Our PO reference is {po}." if po else "No PO number for this one."
    body = (
        f"Subject: New order - {company}\n\n"
        f"Hi team,\n\nCould we please order the following:\n{item_text}\n\n"
        f"{method_text} Required by {_date_text(delivery_date, rng)}.\n"
        f"Deliver to: {addr['line1']}, {addr['city']}, {addr['postcode']}.\n"
        f"{po_text}\n\nThanks,\n{contact}\n{company}"
    )
    tags = ["has_po" if po else "no_po", f"items_{len(lines)}"]
    return {
        "id": f"order-{i:03d}",
        "input": body,
        "expected": {
            "customer_name": company,
            "contact_name": contact,
            "po_number": po,
            "delivery_method": method,
            "required_by": delivery_date.isoformat(),
            "delivery_address": addr,
            "items": lines,
        },
        "tags": tags,
    }


def invoice_case(i: int, rng: random.Random) -> dict:
    supplier = rng.choice(["Westshire Supplies Ltd", "Pennine Packaging Co", "Solent Hygiene Ltd"])
    company, _ = rng.choice(CUSTOMERS)
    issue = date(2026, 1, 5) + timedelta(days=rng.randint(0, 120))
    terms = rng.choice([14, 30, 60])
    due = issue + timedelta(days=terms)
    items = rng.sample(PRODUCTS, rng.randint(1, 5))
    lines = []
    for sku, desc, price in items:
        qty = rng.randint(1, 20)
        lines.append(
            {
                "sku": sku,
                "description": desc,
                "quantity": qty,
                "unit_price": price,
                "line_total": round(qty * price, 2),
            }
        )
    subtotal = round(sum(ln["line_total"] for ln in lines), 2)
    vat = round(subtotal * 0.2, 2)
    total = round(subtotal + vat, 2)
    number = f"INV-{issue.year}-{rng.randint(1000, 9999)}"

    rows = "\n".join(
        f"{ln['sku']:<10} {ln['description']:<38} {ln['quantity']:>4} "
        f"£{ln['unit_price']:>8,.2f} £{ln['line_total']:>9,.2f}"
        for ln in lines
    )
    body = (
        f"{supplier.upper()}\nVAT Reg: GB{rng.randint(100000000, 999999999)}\n\n"
        f"TAX INVOICE  {number}\n"
        f"Invoice date: {_date_text(issue, rng)}\n"
        f"Payment terms: {terms} days (due {due.strftime('%d/%m/%Y')})\n\n"
        f"Bill to: {company}\n\n"
        f"{'SKU':<10} {'Description':<38} {'Qty':>4} {'Unit':>9} {'Amount':>10}\n"
        f"{rows}\n\n"
        f"Subtotal: £{subtotal:,.2f}\nVAT @ 20%: £{vat:,.2f}\nTOTAL DUE: £{total:,.2f}\n"
    )
    return {
        "id": f"invoice-{i:03d}",
        "input": body,
        "expected": {
            "invoice_number": number,
            "supplier_name": supplier,
            "customer_name": company,
            "issue_date": issue.isoformat(),
            "due_date": due.isoformat(),
            "currency": "GBP",
            "line_items": lines,
            "subtotal": subtotal,
            "vat": vat,
            "total": total,
        },
        "tags": [f"terms_{terms}", f"lines_{len(lines)}"],
    }


def write(path: Path, cases: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cases) + "\n")


def main(seed: int = 7, n: int = 12) -> None:
    rng = random.Random(seed)
    write(ROOT / "order_extraction" / "cases.jsonl", [order_case(i + 1, rng) for i in range(n)])
    write(ROOT / "invoice_extraction" / "cases.jsonl", [invoice_case(i + 1, rng) for i in range(n)])


if __name__ == "__main__":
    main()
