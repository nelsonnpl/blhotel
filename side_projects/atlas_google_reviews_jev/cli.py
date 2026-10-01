from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from .jev_runner import JevNavigationError, JevUnavailable, collect_with_jev
from .parser import parse_reviews_html


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prueba aislada de reseñas de hoteles con Atlas + Jev.")
    parser.add_argument("--url", required=True, help="URL pública de Google Hotels/Maps del hotel")
    parser.add_argument("--hotel-name", default=None)
    parser.add_argument("--fixture", type=Path, help="Parsea HTML local sin abrir el navegador")
    parser.add_argument("--record-dir", type=Path, help="Directorio opcional para trazas/screenshots de Jev")
    parser.add_argument("--max-reviews", type=int, default=20, help="Máximo de reseñas (1-10000); usa 0 para agotar el recorrido accesible")
    parser.add_argument("--budget-usd", type=float, help="Tope estimado para decisiones Jev de OpenRouter")
    parser.add_argument("--estimated-decision-cost-usd", type=float, help="Estimación por decisión Jev configurada por el operador")
    parser.add_argument("--max-decisions", type=int, default=24, help="Máximo de decisiones Jev para el hotel (1-120)")
    parser.add_argument("--checkpoint", type=Path, help="Checkpoint JSON reemplazado de forma atómica durante la captura")
    parser.add_argument("--output", type=Path, help="Archivo JSON de salida; si falta, imprime en stdout")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    def save_checkpoint(result) -> None:
        if not args.checkpoint:
            return
        args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.checkpoint.with_suffix(args.checkpoint.suffix + ".tmp")
        temporary.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, args.checkpoint)
    try:
        if args.fixture:
            result = parse_reviews_html(
                args.fixture.read_text(encoding="utf-8"),
                source_url=args.url,
                final_url=args.url,
                captured_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                fallback_hotel_name=args.hotel_name,
            )
        else:
            result = collect_with_jev(
                args.url, hotel_name=args.hotel_name,
                record_dir=str(args.record_dir) if args.record_dir else None,
                max_reviews=args.max_reviews or None, budget_usd=args.budget_usd,
                estimated_decision_cost_usd=args.estimated_decision_cost_usd,
                max_decisions=args.max_decisions,
                checkpoint=save_checkpoint if args.checkpoint else None,
            )
    except (JevUnavailable, JevNavigationError, OSError, ValueError) as exc:
        result = {
            "schemaVersion": "atlas.google-reviews.v1",
            "status": "parse_error",
            "sourceUrl": args.url,
            "reviews": [],
            "message": str(exc),
        }
    else:
        result = result.model_dump(mode="json")

    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    return 0 if result.get("status") in {"ok", "empty", "blocked", "partial", "exhausted", "budget_exhausted"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
