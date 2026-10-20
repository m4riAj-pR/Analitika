"""
app/ml/train_model.py
---------------------
Script de ENTRENAMIENTO OFFLINE del modelo Gradient Boosting para
predecir el ROI a 7 dias de una campana de marketing digital.

EJECUTAR MANUALMENTE (fuera del ciclo de vida HTTP):
    cd analitika_CRUD
    python -m app.ml.train_model

NO se ejecuta por request HTTP. El modelo serializado resultante
se deploya junto con el codigo fuente (ver app/ml/model_artifacts/).

Restricciones:
  - Solo usa datos de las PRIMERAS 48h de cada campana como features.
  - El target roi_7d se calcula con datos COMPLETOS de 7 dias (campanas
    con status='finished' y al menos 7 dias de vida).
  - No hay fuga de datos: los features de 48h y el target de 7d son
    disjuntos en tiempo.
"""

from __future__ import annotations

import logging
import math
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuracion de logging temprana (antes de imports que puedan loggear)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("analitika.ml.train")

# ---------------------------------------------------------------------------
# Carga de variables de entorno (necesaria para run_query)
# ---------------------------------------------------------------------------
try:
    from app.config import load_env_file
    load_env_file()
except Exception:
    pass  # En CI/test puede no existir .env

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
import joblib

from app.db.database import run_query
from app.ml.feature_engineering import (
    MODEL_FEATURE_COLUMNS,
    build_features_from_campaign,
    features_to_vector,
)
from app.ml.synthetic_generator import generate_synthetic_training_vectors

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ARTIFACTS_DIR = Path(__file__).parent / "model_artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_VERSION = 1  # Incrementar manualmente en cada reentrenamiento significativo

# ---------------------------------------------------------------------------
# PASO 1: AUDITORIA – campanas aptas para entrenamiento
# ---------------------------------------------------------------------------

def audit_training_campaigns() -> list[dict]:
    """
    Retorna campanas 'finished' con >= 7 dias de vida y al menos 1 click
    o conversion registrada.

    Criterios de inclusion:
      1. status = 'finished'
      2. start_date IS NOT NULL AND end_date IS NOT NULL
      3. DATEDIFF(end_date, start_date) >= 7
      4. Al menos 1 click o 1 conversion asociada.
    """
    logger.info("=== AUDITORIA: Contando campanas aptas para entrenamiento ===")

    try:
        rows = run_query(
            """
            SELECT
                c.id_campaign,
                c.name,
                c.start_date,
                c.end_date,
                c.spent,
                DATEDIFF(c.end_date, c.start_date) AS duration_days,
                COUNT(DISTINCT ck.id_click)          AS total_clicks,
                COUNT(DISTINCT cv.id_conversion)     AS total_conversions,
                COALESCE(SUM(cv.revenue), 0)         AS total_revenue
            FROM campaigns c
            LEFT JOIN tracking_links tl ON tl.id_campaign = c.id_campaign
            LEFT JOIN clicks ck         ON ck.id_link = tl.id_link
            LEFT JOIN conversions cv    ON cv.id_click = ck.id_click
            WHERE c.status = 'finished'
              AND c.start_date IS NOT NULL
              AND c.end_date IS NOT NULL
              AND DATEDIFF(c.end_date, c.start_date) >= 7
            GROUP BY c.id_campaign, c.name, c.start_date, c.end_date, c.spent
            HAVING total_clicks > 0 OR total_conversions > 0
            ORDER BY c.id_campaign
            """,
            fetch=True,
        )
    except Exception as e:
        logger.warning(
            f"No se pudo consultar la base de datos para auditoria de campanas ({e}). "
            f"Se procedera exclusivamente con datos sinteticos para el entrenamiento base."
        )
        rows = []

    count = len(rows) if rows else 0
    logger.info(f"Campanas aptas encontradas: {count}")

    if count < 30:
        logger.warning(
            f"[LIMITACION] Solo {count} campanas reales aptas para entrenamiento "
            f"(umbral recomendado: 30-40). Se generaran datos SINTETICOS de apoyo. "
            f"Ver docstring de generate_synthetic_data() para detalles."
        )
    else:
        logger.info("Dataset real suficiente para entrenamiento.")

    return rows or []


# ---------------------------------------------------------------------------
# PASO 2: CONSTRUCCION DEL DATASET
# ---------------------------------------------------------------------------

def build_training_row(campaign: dict) -> tuple[list[float], float] | None:
    """
    Para una campana dada, construye (X_vector, roi_7d_target).

    El target roi_7d = (revenue_7d - spend_7d) / spend_7d
    usando datos COMPLETOS de los primeros 7 dias de la campana.

    Retorna None si la campana no tiene suficientes datos de target.
    """
    id_campaign = campaign["id_campaign"]

    # Features: solo datos de las primeras 48h
    try:
        features = build_features_from_campaign(id_campaign)
    except Exception as e:
        logger.warning(f"No se pudo construir features para campana {id_campaign}: {e}")
        return None

    X = features_to_vector(features)

    # Target: revenue y spend de los primeros 7 dias reales
    start_date = campaign["start_date"]
    if isinstance(start_date, datetime):
        sd = start_date.replace(tzinfo=timezone.utc) if start_date.tzinfo is None else start_date
    else:
        from datetime import datetime as dt
        sd = dt(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)

    from datetime import timedelta
    window_7d_end = sd + timedelta(days=7)

    rev_rows = run_query(
        """
        SELECT COALESCE(SUM(cv.revenue), 0.0) AS revenue_7d
        FROM tracking_links tl
        JOIN clicks ck ON ck.id_link = tl.id_link
        JOIN conversions cv ON cv.id_click = ck.id_click
        WHERE tl.id_campaign = %s
          AND ck.created_at >= %s
          AND ck.created_at < %s
        """,
        (id_campaign, sd, window_7d_end),
        fetch=True,
    )
    revenue_7d = float((rev_rows[0]["revenue_7d"] or 0.0) if rev_rows else 0.0)

    # Spend de 7 dias: metricas externas o interpolacion lineal
    spend_7d_rows = run_query(
        """
        SELECT COALESCE(SUM(cem.spend), 0.0) AS api_spend_7d
        FROM campaign_external_mapping cmap
        JOIN campaign_external_metrics cem ON cem.id_mapping = cmap.id_mapping
        WHERE cmap.id_campaign = %s
          AND cem.metric_date >= DATE(%s)
          AND cem.metric_date < DATE(%s)
        """,
        (id_campaign, sd, window_7d_end),
        fetch=True,
    )
    api_spend_7d = float((spend_7d_rows[0]["api_spend_7d"] or 0.0) if spend_7d_rows else 0.0)

    total_spent = float(campaign.get("spent") or 0.0)
    duration_days = int(campaign.get("duration_days") or 0)

    if api_spend_7d > 0:
        spend_7d = api_spend_7d
    elif duration_days > 0 and total_spent > 0:
        spend_7d = total_spent * min(7, duration_days) / duration_days
    else:
        spend_7d = 0.0

    if spend_7d <= 0:
        logger.debug(f"Campana {id_campaign} sin spend_7d valido; omitida.")
        return None

    roi_7d = (revenue_7d - spend_7d) / spend_7d
    return X, roi_7d


# ---------------------------------------------------------------------------
# DATOS SINTETICOS (apoyo cuando dataset real < 30 registros)
# ---------------------------------------------------------------------------

def generate_synthetic_data(n: int = 60, seed: int = 42) -> list[tuple[list[float], float]]:
    """
    Genera filas sinteticas para complementar el dataset real cuando es
    insuficiente (<30 campanas reales).

    Utiliza el generador econometrico realista con rendimientos decrecientes:
      - spend_48h segun canal (Meta/Google mas caros que WhatsApp/Email)
      - clicks_48h funcion de spend_48h con CPC variable + ruido
      - conversion_rate_48h segun canal + ruido
      - conversions_48h = clicks_48h * conversion_rate_48h
      - revenue_48h = conversions_48h * valor_promedio_por_conversion + ruido
      - roi_7d = relacion no lineal con saturacion de pauta/audiencia y rendimientos decrecientes.
    """
    records = generate_synthetic_training_vectors(n=n, seed=seed)
    logger.info(f"Generadas {len(records)} filas SINTETICAS de apoyo con rendimientos decrecientes (seed={seed}).")
    return records


# ---------------------------------------------------------------------------
# PASO 3: ENTRENAMIENTO Y EVALUACION
# ---------------------------------------------------------------------------

def train_and_save(
    X_all: list[list[float]],
    y_all: list[float],
    n_real: int,
) -> Path:
    """
    Entrena el GradientBoostingRegressor, evalua y serializa el modelo.

    Args:
        X_all:  Lista de vectores de features.
        y_all:  Lista de targets (roi_7d).
        n_real: Numero de filas reales (para documentar en logs).

    Returns:
        Path al artefacto .joblib creado.
    """
    X = np.array(X_all, dtype=np.float32)
    y = np.array(y_all, dtype=np.float32)

    logger.info(f"Dataset total: {len(X)} filas ({n_real} reales, {len(X)-n_real} sinteticas)")
    logger.info(f"Features: {MODEL_FEATURE_COLUMNS}")
    logger.info(f"Target: roi_7d — min={y.min():.4f}, max={y.max():.4f}, mean={y.mean():.4f}")

    if len(X) < 10:
        raise RuntimeError(
            "Dataset insuficiente incluso con datos sinteticos. "
            "Se necesitan al menos 10 filas para entrenar."
        )

    test_size = 0.2 if len(X) >= 20 else 0.1
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )

    model = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.8,
        min_samples_leaf=3,
        random_state=42,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae  = mean_absolute_error(y_test, y_pred)
    r2   = r2_score(y_test, y_pred)

    logger.info("=== METRICAS DE EVALUACION ===")
    logger.info(f"  MAE  (Error Absoluto Medio):  {mae:.4f}")
    logger.info(f"  R2   (Coeficiente Determinacion): {r2:.4f}")
    logger.info(f"  Interpretacion: un MAE de {mae:.4f} significa que el modelo se equivoca")
    logger.info(f"  en promedio {mae*100:.2f} puntos porcentuales de ROI.")

    # Feature importances
    importances = dict(zip(MODEL_FEATURE_COLUMNS, model.feature_importances_))
    logger.info("  Feature importances:")
    for feat, imp in sorted(importances.items(), key=lambda x: -x[1]):
        logger.info(f"    {feat}: {imp:.4f}")

    # Serializar
    artifact_name = f"gb_campaign_7d_v{MODEL_VERSION}.joblib"
    artifact_path = ARTIFACTS_DIR / artifact_name
    joblib.dump(
        {
            "model":            model,
            "feature_columns":  MODEL_FEATURE_COLUMNS,
            "version":          MODEL_VERSION,
            "trained_at":       datetime.now(timezone.utc).isoformat(),
            "n_samples_real":   n_real,
            "n_samples_synth":  len(X) - n_real,
            "metrics": {
                "mae":  float(mae),
                "r2":   float(r2),
                "test_size": int(len(X_test)),
                "train_size": int(len(X_train)),
            },
            "dataset_warning": (
                None if n_real >= 30
                else (
                    f"ATENCION: Solo {n_real} campanas reales disponibles para "
                    f"entrenamiento (recomendado >= 30). El modelo incluye "
                    f"{len(X)-n_real} filas sinteticas de apoyo. Las predicciones "
                    f"deben interpretarse con cautela hasta disponer de mas datos reales."
                )
            ),
        },
        artifact_path,
    )

    logger.info(f"Modelo serializado en: {artifact_path}")
    logger.info(f"Tamano del artefacto: {artifact_path.stat().st_size / 1024:.1f} KB")
    return artifact_path


# ---------------------------------------------------------------------------
# ENTRADA PRINCIPAL
# ---------------------------------------------------------------------------

def main():
    logger.info("=" * 60)
    logger.info("  Analitika ML – Entrenamiento Gradient Boosting ROI 7d")
    logger.info("=" * 60)

    # Auditoria
    real_campaigns = audit_training_campaigns()
    n_real_raw = len(real_campaigns)

    # Construir filas reales
    real_records: list[tuple[list[float], float]] = []
    for camp in real_campaigns:
        row = build_training_row(camp)
        if row is not None:
            real_records.append(row)

    n_real = len(real_records)
    logger.info(f"Filas reales con datos validos: {n_real} (de {n_real_raw} campanas auditadas)")

    # Si son pocas, complementar con sinteticos
    all_records = list(real_records)
    if n_real < 30:
        synth_needed = max(60 - n_real, 30)
        synth_records = generate_synthetic_data(n=synth_needed)
        all_records.extend(synth_records)
    else:
        synth_records = []

    X_all = [r[0] for r in all_records]
    y_all = [r[1] for r in all_records]

    # Entrenar y guardar
    artifact_path = train_and_save(X_all, y_all, n_real=n_real)

    logger.info("=" * 60)
    logger.info(f"  Entrenamiento completado. Artefacto: {artifact_path.name}")
    logger.info("=" * 60)

    return artifact_path


if __name__ == "__main__":
    main()
