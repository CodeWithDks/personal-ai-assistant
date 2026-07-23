# backend/normalize_status_casing.py
#
# Run once: python normalize_status_casing.py
# Fixes any existing rows where status was stored with inconsistent casing
# (e.g. "Pending" instead of "pending") so they match the TaskStatus enum.

from backend.app.database.database import SessionLocal
from backend.app.database.models import Task

db = SessionLocal()

try:
    tasks = db.query(Task).all()
    fixed = 0

    for task in tasks:
        if task.status and task.status != task.status.lower():
            task.status = task.status.lower()
            fixed += 1

    db.commit()
    print(f"Normalized {fixed} task(s).")

finally:
    db.close()