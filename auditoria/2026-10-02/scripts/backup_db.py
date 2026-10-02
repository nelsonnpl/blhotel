#!/usr/bin/env python3
"""Backup de SQLite con API online + integrity_check + sha256 + recuentos.

Uso:
  python3 backup_db.py <origen.sqlite> <destino.sqlite> [--dry-run]
  Sin args: origen ./data/booking-prices.sqlite, destino backups/pulido-<fecha>.sqlite
Nunca imprime secretos. Solo stdlib.
"""
import hashlib
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    dry = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    src = Path(args[0]) if len(args) > 0 else Path("./data/booking-prices.sqlite")
    if len(args) > 1:
        dst = Path(args[1])
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        dst = Path(f"./backups/pulido-{stamp}.sqlite")
    if not src.exists():
        print(f"MAL no existe origen {src}")
        return 1
    if dry:
        con = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
        try:
            print("integrity_check:", con.execute("PRAGMA integrity_check").fetchone()[0])
            tables = [r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
            for t in sorted(tables):
                print(f"filas {t}: {con.execute(f'SELECT COUNT(*) FROM \"{t}\"').fetchone()[0]}")
        finally:
            con.close()
        print(f"OK seco sobre {src} sha256={sha256(src)[:16]}…")
        return 0
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".tmp.sqlite")
    src_con = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    try:
        if src_con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            print("MAL integrity_check previo distinto de ok")
            return 1
        dst_con = sqlite3.connect(str(tmp))
        try:
            src_con.backup(dst_con)
        finally:
            dst_con.close()
    finally:
        src_con.close()
    dst_con = sqlite3.connect(str(tmp))
    try:
        check = dst_con.execute("PRAGMA integrity_check").fetchone()[0]
        tables = [r[0] for r in dst_con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        counts = {t: dst_con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables}
    finally:
        dst_con.close()
    if check != "ok":
        tmp.unlink(missing_ok=True)
        print("MAL integrity_check del backup")
        return 1
    shutil.move(str(tmp), str(dst))
    print(f"OK {dst} sha256={sha256(dst)}")
    for t in sorted(counts):
        print(f"filas {t}: {counts[t]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
