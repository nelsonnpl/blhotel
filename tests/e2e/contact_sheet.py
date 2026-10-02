"""Hoja de contacto HTML con todas las capturas de una carpeta (parada 2).

Uso: .venv/bin/python tests/e2e/contact_sheet.py <carpeta-png> [--out hoja.html]
"""
import argparse
from pathlib import Path

CSS = "body{font-family:sans-serif;background:#111;color:#eee;margin:0}h1{font-size:15px;padding:12px 16px;margin:0}img{width:100%;border:1px solid #333}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:12px;padding:0 16px 16px}figure{margin:0}figcaption{font-size:12px;padding:4px 0}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    carpeta = Path(args.carpeta)
    pngs = sorted(carpeta.glob("*.png"))
    out = Path(args.out) if args.out else carpeta / "contacto.html"
    figs = "\n".join(
        f'<figure><figcaption>{p.name}</figcaption><img loading="lazy" src="{p.name}"></figure>'
        for p in pngs)
    out.write_text(f"<!doctype html><meta charset=utf-8><title>{carpeta.name}</title>"
                   f"<style>{CSS}</style><h1>{carpeta.name} · {len(pngs)} capturas</h1><main>{figs}</main>")
    print(f"OK {out} ({len(pngs)} capturas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
