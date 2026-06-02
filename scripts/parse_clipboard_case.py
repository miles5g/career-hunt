"""Parse Soft Skillet ticket export from markdown table."""
import re
from collections import defaultdict
from pathlib import Path
from statistics import median

RAW = Path(r"C:\Users\owner\.cursor\projects\c-Users-owner-Documents-Cursor-Projects-Career\uploads\edit-0.md")


def parse_row(parts: list[str]) -> dict | None:
    if len(parts) < 10:
        return None
    tid = parts[2].strip()
    if not re.fullmatch(r"[a-z0-9]{6}", tid):
        return None
    channel = parts[7].strip()
    call_status = parts[9].strip() if channel == "Phone" else ""
    ticket_type = ""
    satisfaction = ""
    qa = ""
    first_reply = ""
    handle_sec = ""

    if channel == "Phone":
        if call_status == "Connected" and len(parts) > 13:
            first_reply = parts[10].strip()
            handle_sec = parts[10].strip()  # connected: col 10 is first reply per dict? 
            # Dictionary: J=first reply email, K=handling time
            # Connected phone row: 10=208 first reply? Actually mdu464: 10=208, 11=type, no separate handle in short rows
            # Check if 11 is numeric handle
            if parts[11].strip().isdigit():
                handle_sec = parts[11].strip()
                ticket_type = parts[12].strip() if len(parts) > 12 else ""
                satisfaction = parts[13].strip() if len(parts) > 13 else ""
                qa = parts[14].strip() if len(parts) > 14 else ""
            else:
                ticket_type = parts[11].strip()
                satisfaction = parts[12].strip() if len(parts) > 12 else ""
                qa = parts[13].strip() if len(parts) > 13 else ""
                if parts[10].strip().isdigit():
                    first_reply = parts[10].strip()
        elif call_status == "Abandoned":
            pass
    elif channel == "Email":
        if len(parts) > 12:
            first_reply = parts[9].strip()
            if parts[10].strip().isdigit():
                handle_sec = parts[10].strip()
                ticket_type = parts[11].strip()
                satisfaction = parts[12].strip()
                qa = parts[13].strip() if len(parts) > 13 else ""
            else:
                ticket_type = parts[10].strip()
                satisfaction = parts[11].strip()
                qa = parts[12].strip() if len(parts) > 12 else ""
                if parts[9].strip().isdigit() and not ticket_type:
                    first_reply = parts[9].strip()

    return {
        "ticket_id": tid,
        "account": parts[3].strip(),
        "agent": parts[5].strip(),
        "team": parts[6].strip(),
        "channel": channel,
        "queue_sec": parts[8].strip(),
        "call_status": call_status,
        "first_reply": first_reply,
        "handle_sec": handle_sec,
        "ticket_type": ticket_type,
        "satisfaction": satisfaction,
        "qa": qa,
    }


def load_rows() -> list[dict]:
    text = RAW.read_text(encoding="utf-8")
    rows = []
    for line in text.splitlines():
        if "Ticket ID" in line or line.strip().startswith("|---"):
            continue
        parts = [p.strip() for p in line.split("|")]
        row = parse_row(parts)
        if row:
            rows.append(row)
    return rows


def score_agent(rows: list[dict], ag: str) -> dict:
    ar = [r for r in rows if r["agent"] == ag]
    phone = [r for r in ar if r["channel"] == "Phone"]
    email = [r for r in ar if r["channel"] == "Email"]
    abandoned = sum(1 for r in phone if r["call_status"] == "Abandoned")
    connected = [r for r in phone if r["call_status"] == "Connected"]
    phone_total = len(phone)
    handles = [int(r["handle_sec"]) for r in connected if r["handle_sec"].isdigit()]
    qas = [int(r["qa"]) for r in ar if r["qa"].isdigit()]
    unsat = sum(1 for r in ar if r["satisfaction"] == "Unsatisfied")
    sat_ok = sum(1 for r in ar if r["satisfaction"] == "Satisfied")
    rated = sum(
        1
        for r in ar
        if r["satisfaction"] in ("Satisfied", "Unsatisfied", "Offered", "Not Offered")
    )
    email_reply = [int(r["first_reply"]) for r in email if r["first_reply"].isdigit()]
    abandon_pct = 100 * abandoned / phone_total if phone_total else 0
    med_handle = int(median(handles)) if handles else None
    avg_qa = sum(qas) / len(qas) if qas else None
    med_reply = int(median(email_reply)) if email_reply else None
    pts = 0.0
    if phone_total:
        pts += (100 - abandon_pct) * 0.4
    if handles and med_handle is not None:
        pts += max(0, (500 - med_handle) / 500) * 20
    if qas and avg_qa is not None:
        pts += avg_qa * 8
    if rated:
        pts += (sat_ok / rated) * 15
        pts -= (unsat / rated) * 10
    if email_reply and med_reply is not None:
        pts += max(0, (900 - med_reply) / 900) * 10
    return dict(
        tickets=len(ar),
        abandon_pct=abandon_pct,
        phone=phone_total,
        abandoned=abandoned,
        connected=len(connected),
        med_handle=med_handle,
        avg_qa=round(avg_qa, 2) if avg_qa is not None else None,
        qa_n=len(qas),
        unsat=unsat,
        sat=sat_ok,
        rated=rated,
        med_reply=med_reply,
        pts=pts,
    )


def main() -> None:
    rows = load_rows()
    n = len(rows)
    print(f"Total tickets: {n}")

    type_counts = defaultdict(int)
    for r in rows:
        if r["ticket_type"]:
            type_counts[r["ticket_type"]] += 1
    print("\n=== Ticket types ===")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"{c:3d} ({100*c/n:4.1f}%)  {t}")

    res_types = ("Missing / Incorrect Reservations", "Overbooking / Double-Booking")
    res_count = sum(type_counts[t] for t in res_types)
    billing = type_counts.get("Billing / Subscription Issue", 0)
    print(f"\nReservation cluster: {res_count} ({100*res_count/n:.1f}%)")
    print(f"Billing: {billing} ({100*billing/n:.1f}%)")

    agents = sorted(set(r["agent"] for r in rows))
    print("\n=== Agent ranking (composite) ===")
    ranked = sorted(agents, key=lambda a: score_agent(rows, a)["pts"], reverse=True)
    for i, ag in enumerate(ranked, 1):
        s = score_agent(rows, ag)
        mh = s["med_handle"] if s["med_handle"] is not None else "-"
        print(
            f"{i:2d}. {ag:14s}  n={s['tickets']:2d}  abandon={s['abandon_pct']:5.1f}%  "
            f"med_handle={mh}  avg_qa={s['avg_qa']}  pts={s['pts']:.1f}"
        )

    print("\n=== Unsatisfied rate by type (rated tickets) ===")
    for t in sorted(type_counts, key=type_counts.get, reverse=True)[:8]:
        tr = [r for r in rows if r["ticket_type"] == t and r["satisfaction"]]
        if not tr:
            continue
        u = sum(1 for r in tr if r["satisfaction"] == "Unsatisfied")
        print(f"  {t}: {u}/{len(tr)} ({100*u/len(tr):.0f}%)")

    acct = defaultdict(int)
    for r in rows:
        acct[r["account"]] += 1
    print("\n=== Accounts with 3+ tickets ===")
    for a, c in sorted(acct.items(), key=lambda x: -x[1]):
        if c >= 3:
            types = [r["ticket_type"] for r in rows if r["account"] == a and r["ticket_type"]]
            print(f"  {a}: {c} tickets  types={types[:4]}")

    total_phone = sum(1 for r in rows if r["channel"] == "Phone")
    total_abandon = sum(1 for r in rows if r["call_status"] == "Abandoned")
    print(f"\nPhone abandon overall: {total_abandon}/{total_phone} ({100*total_abandon/total_phone:.1f}%)")

    queues = [int(r["queue_sec"]) for r in rows if r["channel"] == "Phone" and r["queue_sec"].isdigit()]
    if queues:
        print(f"Phone queue median (sec): {int(median(queues))}")


if __name__ == "__main__":
    main()
