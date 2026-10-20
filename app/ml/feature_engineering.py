"""
app/ml/feature_engineering.py
------------------------------
Construccion de features por campana a partir de datos observables
en las PRIMERAS 48 HORAS desde start_date.

Esta funcion es la UNICA fuente de verdad para feature engineering:
se usa tanto en entrenamiento (train_model.py) como en inferencia
(predictor_service.py), evitando discrepancias entre features de
train y de produccion (fuga de datos / training-serving skew).

RESTRICCION CRITICA: No se usan datos posteriores a las 48h como
feature. El target roi_7d se calcula por separado SOLO durante el
entrenamiento y NUNCA se filtra aqui.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.db.database import run_query

logger = logging.getLogger(__name__)

# Ventana de observacion en horas (configurable para tests)
OBSERVATION_WINDOW_HOURS: int = 48

# Codificacion de canales conocidos (label encoding estable)
CHANNEL_ENCODING: dict[str, int] = {
    "meta":        1,
    "facebook":    1,
    "google":      2,
    "tiktok":      3,
    "email":       4,
    "organic":     5,
    "direct":      6,
    "whatsapp":    7,
    "other":       0,
    "desconocido": 0,
}


class InsufficientDataError(ValueError):
    """Se lanza cuando la campana no tiene suficientes datos de las 48h."""
    pass


def _encode_channel(channel_name: Optional[str]) -> int:
    """Codifica el nombre del canal a un entero."""
    if not channel_name:
        return 0
    return CHANNEL_ENCODING.get(channel_name.lower().strip(), 0)


def build_features_from_campaign(
    id_campaign: int,
    observation_hours: int = OBSERVATION_WINDOW_HOURS,
) -> dict:
    """
    Construye el vector de features para una campana dado su id.

    Solo usa datos dentro de la ventana [start_date, start_date + observation_hours].
    Si la campana no tiene start_date o aun no han pasado 48h, devuelve
    el vector con los datos disponibles y marca 'has_full_observation_window=False'.

    Args:
        id_campaign: PK de la campana en la tabla campaigns.
        observation_hours: Horas de la ventana de observacion (default 48).

    Returns:
        dict con las siguientes claves:
          - id_campaign (int)
          - clicks_48h (int)
          - conversions_48h (int)
          - revenue_48h (float)
          - conversion_rate_48h (float)  # conversions/clicks, 0 si clicks==0
          - spend_48h (float)            # spend proporcional a las horas transcurridas
          - channel_encoded (int)        # label encoding del canal principal
          - campaign_duration_days (int) # duracion total en dias (0 si no tiene end_date)
          - has_full_observation_window (bool)
          - hours_elapsed (float)        # horas reales disponibles
          - start_date (str | None)      # ISO date string
    """
    # ------------------------------------------------------------------ #
    # 1. Datos de la campana
    # ------------------------------------------------------------------ #
    camp_rows = run_query(
        """
        SELECT c.id_campaign, c.start_date, c.end_date, c.spent,
               ch.name AS channel_name
        FROM campaigns c
        LEFT JOIN tracking_links tl ON tl.id_campaign = c.id_campaign
        LEFT JOIN channels ch ON tl.id_channel = ch.id_channel
        WHERE c.id_campaign = %s
        LIMIT 1
        """,
        (id_campaign,),
        fetch=True,
    )

    if not camp_rows:
        raise ValueError(f"Campana {id_campaign} no encontrada.")

    camp = camp_rows[0]
    start_date = camp["start_date"]   # puede ser None o date/datetime
    end_date   = camp["end_date"]
    total_spent = float(camp["spent"] or 0.0)
    channel_name = camp.get("channel_name")

    # Calcular ventana de observacion
    now = datetime.now(timezone.utc)

    if start_date is None:
        # Sin start_date no podemos delimitar la ventana
        return {
            "id_campaign":               id_campaign,
            "clicks_48h":                0,
            "conversions_48h":           0,
            "revenue_48h":               0.0,
            "conversion_rate_48h":       0.0,
            "spend_48h":                 0.0,
            "channel_encoded":           _encode_channel(channel_name),
            "campaign_duration_days":    0,
            "has_full_observation_window": False,
            "hours_elapsed":             0.0,
            "start_date":                None,
        }

    # Normalizar start_date a datetime con tz
    if isinstance(start_date, datetime):
        sd = start_date.replace(tzinfo=timezone.utc) if start_date.tzinfo is None else start_date
    else:
        # date object
        sd = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)

    observation_end = sd + timedelta(hours=observation_hours)
    hours_elapsed = max(0.0, min((now - sd).total_seconds() / 3600.0, float(observation_hours)))
    has_full_window = now >= observation_end

    # Duracion total de la campana (para features contextuales)
    if end_date:
        if isinstance(end_date, datetime):
            ed = end_date.replace(tzinfo=timezone.utc) if end_date.tzinfo is None else end_date
        else:
            ed = datetime(end_date.year, end_date.month, end_date.day, tzinfo=timezone.utc)
        campaign_duration_days = max(0, (ed - sd).days)
    else:
        campaign_duration_days = 0

    # ------------------------------------------------------------------ #
    # 2. Clicks dentro de la ventana de 48h (via tracking_links)
    # ------------------------------------------------------------------ #
    click_rows = run_query(
        """
        SELECT COUNT(ck.id_click) AS clicks_48h
        FROM tracking_links tl
        JOIN clicks ck ON ck.id_link = tl.id_link
        WHERE tl.id_campaign = %s
          AND ck.created_at >= %s
          AND ck.created_at < %s
        """,
        (id_campaign, sd, observation_end),
        fetch=True,
    )
    clicks_48h = int((click_rows[0]["clicks_48h"] or 0) if click_rows else 0)

    # ------------------------------------------------------------------ #
    # 3. Conversiones y revenue dentro de la ventana de 48h
    # ------------------------------------------------------------------ #
    conv_rows = run_query(
        """
        SELECT COUNT(cv.id_conversion) AS conversions_48h,
               COALESCE(SUM(cv.revenue), 0.0) AS revenue_48h
        FROM tracking_links tl
        JOIN clicks ck ON ck.id_link = tl.id_link
        JOIN conversions cv ON cv.id_click = ck.id_click
        WHERE tl.id_campaign = %s
          AND ck.created_at >= %s
          AND ck.created_at < %s
        """,
        (id_campaign, sd, observation_end),
        fetch=True,
    )
    conversions_48h = int((conv_rows[0]["conversions_48h"] or 0) if conv_rows else 0)
    revenue_48h     = float((conv_rows[0]["revenue_48h"] or 0.0) if conv_rows else 0.0)

    # ------------------------------------------------------------------ #
    # 4. Spend proporcional a las horas observadas vs duracion total
    # ------------------------------------------------------------------ #
    # Si hay metricas externas por dia, las usamos para mayor precision.
    # Caso base: interpolacion lineal del spend total.
    spend_48h_raw = run_query(
        """
        SELECT COALESCE(SUM(cem.spend), 0.0) AS api_spend_48h
        FROM campaign_external_mapping cmap
        JOIN campaign_external_metrics cem ON cem.id_mapping = cmap.id_mapping
        WHERE cmap.id_campaign = %s
          AND cem.metric_date >= DATE(%s)
          AND cem.metric_date < DATE(%s)
        """,
        (id_campaign, sd, observation_end),
        fetch=True,
    )
    api_spend = float((spend_48h_raw[0]["api_spend_48h"] or 0.0) if spend_48h_raw else 0.0)

    if api_spend > 0:
        spend_48h = api_spend
    elif campaign_duration_days > 0 and total_spent > 0:
        # Interpolacion lineal: (horas_observadas / horas_totales) * spend_total
        total_hours = campaign_duration_days * 24.0
        spend_48h = total_spent * min(hours_elapsed, observation_hours) / total_hours
    else:
        spend_48h = 0.0

    # ------------------------------------------------------------------ #
    # 5. Tasa de conversion
    # ------------------------------------------------------------------ #
    conversion_rate_48h = conversions_48h / clicks_48h if clicks_48h > 0 else 0.0

    # ------------------------------------------------------------------ #
    # 6. Canal principal (label encoding)
    # ------------------------------------------------------------------ #
    channel_encoded = _encode_channel(channel_name)

    return {
        "id_campaign":                id_campaign,
        "clicks_48h":                 clicks_48h,
        "conversions_48h":            conversions_48h,
        "revenue_48h":                revenue_48h,
        "conversion_rate_48h":        conversion_rate_48h,
        "spend_48h":                  spend_48h,
        "channel_encoded":            channel_encoded,
        "campaign_duration_days":     campaign_duration_days,
        "has_full_observation_window": has_full_window,
        "hours_elapsed":              hours_elapsed,
        "start_date":                 sd.date().isoformat() if start_date else None,
    }


# Columnas que el modelo espera (en orden fijo para evitar skew)
MODEL_FEATURE_COLUMNS: list[str] = [
    "clicks_48h",
    "conversions_48h",
    "revenue_48h",
    "conversion_rate_48h",
    "spend_48h",
    "channel_encoded",
    "campaign_duration_days",
]


def features_to_vector(features: dict) -> list[float]:
    """
    Convierte el dict de features al vector ordenado que espera el modelo.
    Uso idempotente: misma funcion en train y en inferencia.
    """
    return [float(features.get(col, 0.0)) for col in MODEL_FEATURE_COLUMNS]
