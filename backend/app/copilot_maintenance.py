"""Mantenimiento explícito de la telemetría de Revenue Copilot.

No se ejecuta desde una petición web: evita borrar auditoría por sorpresa y
permite programarlo externamente con la política de retención configurada.
"""

from __future__ import annotations

import argparse
import json

from .config import load_settings
from .database import Database


def main() -> int:
    parser = argparse.ArgumentParser(description="Mantenimiento de auditoría de Revenue Copilot.")
    parser.add_argument("--purge-audit", action="store_true", help="Elimina solo assistant_runs vencidos; no borra conversaciones.")
    args = parser.parse_args()
    if not args.purge_audit:
        parser.error("Indica --purge-audit para confirmar la purga de telemetría.")
    runtime = load_settings(require_decodo=False)
    removed = Database(runtime.sqlite_path).purge_assistant_runs(runtime.copilot_audit_retention_days)
    print(json.dumps({"removed": removed, "retentionDays": runtime.copilot_audit_retention_days}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
