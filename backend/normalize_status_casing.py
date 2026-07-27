# backend/normalize_status_casing.py
#
# Run once: python normalize_status_casing.py
# Fixes any existing rows where status or priority was stored with
# inconsistent casing (e.g. "Pending" instead of "pending", "High"
# instead of "high") so they match the TaskStatus / TaskPriority enums.
#
# Safe to re-run — rows that are already lowercase are left untouched,
# and it reports 0 fixed if there's nothing to do.
#
# Preview changes first (no writes):
#   python normalize_status_casing.py --dry-run
#
# Apply changes:
#   python normalize_status_casing.py

import argparse
import logging

from backend.app.database.database import SessionLocal
from backend.app.database.models import Task

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def normalize_casing(dry_run: bool = False) -> tuple[int, int]:
    """
    Lowercase any Task.status / Task.priority values that aren't already
    lowercase. Returns (status_fixed_count, priority_fixed_count).

    dry_run=True logs what WOULD change without committing anything.
    """

    db = SessionLocal()
    status_fixed = 0
    priority_fixed = 0

    try:
        tasks = db.query(Task).all()
        logger.info("Scanning %d task(s)...", len(tasks))

        for task in tasks:
            if task.status and task.status != task.status.lower():
                logger.info(
                    "Task %s: status %r -> %r", task.id, task.status, task.status.lower()
                )
                if not dry_run:
                    task.status = task.status.lower()
                status_fixed += 1

            if task.priority and task.priority != task.priority.lower():
                logger.info(
                    "Task %s: priority %r -> %r", task.id, task.priority, task.priority.lower()
                )
                if not dry_run:
                    task.priority = task.priority.lower()
                priority_fixed += 1

        if dry_run:
            db.rollback()  # discard any in-memory changes, just in case
            logger.info(
                "[DRY RUN] Would normalize %d status value(s) and %d priority value(s). "
                "No changes were saved — re-run without --dry-run to apply.",
                status_fixed,
                priority_fixed,
            )
        else:
            db.commit()
            logger.info(
                "Normalized %d status value(s) and %d priority value(s).",
                status_fixed,
                priority_fixed,
            )

        return status_fixed, priority_fixed

    except Exception:
        db.rollback()
        logger.exception("Failed to normalize task casing — no changes were saved.")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Normalize casing of Task.status and Task.priority values in the database."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing to the database.",
    )
    args = parser.parse_args()

    normalize_casing(dry_run=args.dry_run)