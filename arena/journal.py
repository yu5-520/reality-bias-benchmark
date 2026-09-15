"""Durable evidence checkpointing; does not feed observations back to agents."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from .core import stable_hash


class Journal:
    def __init__(self, path):
        self.path = Path(path)
        self.previous = None
        self.sequence = 0

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open('x', encoding='utf-8')
        return self

    def __call__(self, record):
        row = dict(record, sequence=self.sequence, previous_hash=self.previous,
                   recorded_at=datetime.now(timezone.utc).isoformat())
        row['record_hash'] = stable_hash(row)
        self.file.write(json.dumps(row, ensure_ascii=False) + '\n')
        self.file.flush()
        os.fsync(self.file.fileno())
        self.previous = row['record_hash']
        self.sequence += 1

    def __exit__(self, *args):
        self.file.close()
