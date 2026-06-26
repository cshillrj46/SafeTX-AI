# File: backend/export_data.py

import csv
from backend.database import SessionLocal, TransactionRecord, ReclassificationLog


def export_transactions_to_csv(filename="transactions.csv"):
    db = SessionLocal()
    records = db.query(TransactionRecord).all()

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["id", "sender", "recipient", "amount_eth", "risk"])
        for r in records:
            writer.writerow([r.id, r.sender, r.recipient, r.amount_eth, r.risk])

    print(f"[Export] Transactions exported to {filename}")


def export_reclassifications_to_csv(filename="reclassifications.csv"):
    db = SessionLocal()
    logs = db.query(ReclassificationLog).all()

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["id", "transaction_id", "old_risk", "new_risk", "reason", "reclassified_by"])
        for r in logs:
            writer.writerow([r.id, r.transaction_id, r.old_risk, r.new_risk, r.reason, r.reclassified_by])

    print(f"[Export] Reclassifications exported to {filename}")


if __name__ == "__main__":
    export_transactions_to_csv()
    export_reclassifications_to_csv()
