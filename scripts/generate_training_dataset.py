"""
scripts/generate_training_dataset.py
-----------------------------------
Script CLI para generar el dataset de entrenamiento sintetico
basado en especificaciones econometricas para campanas de marketing digital.

Uso:
    python scripts/generate_training_dataset.py
    python scripts/generate_training_dataset.py --n 1000 --output app/ml/data/training_dataset.csv
"""

import argparse
import sys
from pathlib import Path

# Agregar la raiz del proyecto al path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.ml.synthetic_generator import (
    CHANNEL_PROFILES,
    generate_synthetic_dataset,
    save_dataset_to_csv,
)


def print_dataset_summary(dataset: list[dict]):
    """Imprime un resumen estadistico por canal del dataset generado."""
    by_channel: dict[str, list[dict]] = {}
    for row in dataset:
        ch = row["channel_name"]
        by_channel.setdefault(ch, []).append(row)

    print("\n" + "=" * 90)
    print(f"{'RESUMEN ESTADISTICO POR CANAL (' + str(len(dataset)) + ' campanas)':^90}")
    print("=" * 90)
    header = f"{'Canal':<12} | {'Count':<6} | {'Avg Spend 48h':<14} | {'Avg Clicks':<11} | {'Avg CR 48h':<11} | {'Avg Rev 48h':<12} | {'Avg ROI 7d':<11}"
    print(header)
    print("-" * 90)

    for ch, rows in sorted(by_channel.items()):
        count = len(rows)
        avg_spend = sum(r["spend_48h"] for r in rows) / count
        avg_clicks = sum(r["clicks_48h"] for r in rows) / count
        avg_cr = (sum(r["conversion_rate_48h"] for r in rows) / count) * 100.0
        avg_rev = sum(r["revenue_48h"] for r in rows) / count
        avg_roi = (sum(r["roi_7d"] for r in rows) / count) * 100.0

        print(
            f"{ch:<12} | {count:<6} | ${avg_spend:>12.2f} | {avg_clicks:>11.1f} | {avg_cr:>10.2f}% | ${avg_rev:>10.2f} | {avg_roi:>10.1f}%"
        )
    print("=" * 90 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Generador de dataset sintetico para Analitika ML")
    parser.add_argument("--n", type=int, default=500, help="Numero de campanas a simular (default: 500)")
    parser.add_argument("--seed", type=int, default=42, help="Semilla pseudoaleatoria (default: 42)")
    parser.add_argument(
        "--output",
        type=str,
        default=str(ROOT_DIR / "app" / "ml" / "data" / "synthetic_training_dataset.csv"),
        help="Ruta del archivo CSV destino",
    )
    args = parser.parse_args()

    print(f"Generando {args.n} campanas sinteticas con seed={args.seed}...")
    dataset = generate_synthetic_dataset(n=args.n, seed=args.seed)

    output_path = Path(args.output)
    save_dataset_to_csv(dataset, output_path)
    print_dataset_summary(dataset)
    print(f"[OK] Dataset guardado correctamente en: {output_path}")


if __name__ == "__main__":
    main()
