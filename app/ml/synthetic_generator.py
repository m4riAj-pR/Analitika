"""
app/ml/synthetic_generator.py
------------------------------
Generador de dataset sintetico para el modelo predictivo de ROI a 7 dias de Analitika.

Especificaciones implementadas para cada campana:
  1. spend_48h           ~ Distribucion realista segun canal (Meta/Google mas caros que WhatsApp/Email).
  2. clicks_48h          = Funcion de spend_48h con CPC variable por canal + ruido.
  3. conversion_rate_48h ~ Varia por canal (Email/WhatsApp mas alto, Trafico mas bajo) + ruido.
  4. conversions_48h     = clicks_48h * conversion_rate_48h
  5. revenue_48h         = conversions_48h * valor_promedio_por_conversion + ruido.
  6. roi_7d (Objetivo)   = Relacion no lineal con rendimientos decrecientes (saturacion de audiencia/pauta):
                           roi_7d = f(spend_total_proyectado, canal, eficiencia_temprana) + ruido_final.
"""

from __future__ import annotations

import csv
import logging
import math
import os
import random
from pathlib import Path
from typing import Any, Optional

import numpy as np

from app.ml.feature_engineering import CHANNEL_ENCODING, MODEL_FEATURE_COLUMNS

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Perfiles econometricos y parametricos por canal publicitario
# -----------------------------------------------------------------------------
CHANNEL_PROFILES: dict[str, dict[str, Any]] = {
    "meta": {
        "channel_id": CHANNEL_ENCODING["meta"],
        "weight": 0.30,  # 30% del volumen
        # Spend en 48h: Distribucion LogNormal (~$40 a $500, media ~$140)
        "spend_mean_log": 4.85,
        "spend_sigma_log": 0.60,
        "spend_min": 25.0,
        # CPC medio ~$0.65, variacion segun subasta de anuncios
        "cpc_base": 0.65,
        "cpc_sigma": 0.12,
        # Tasa de conversion moderada: Beta(3.0, 97.0) -> ~3.0% (1.5% - 5.5%)
        "cr_alpha": 3.0,
        "cr_beta": 97.0,
        # Ticket promedio (AOV) ~$65 USD
        "aov_mean": 65.0,
        "aov_sigma": 0.25,
        # Capacidad de absorcion antes de saturacion (K_sat)
        "k_sat": 2500.0,
    },
    "google": {
        "channel_id": CHANNEL_ENCODING["google"],
        "weight": 0.25,  # 25% del volumen
        # Spend en 48h: LogNormal (~$50 a $700, media ~$180)
        "spend_mean_log": 5.10,
        "spend_sigma_log": 0.65,
        "spend_min": 35.0,
        # CPC mas alto por intencion de busqueda (~$1.60)
        "cpc_base": 1.60,
        "cpc_sigma": 0.25,
        # Tasa de conversion alta por intencion directa: Beta(4.5, 95.5) -> ~4.5%
        "cr_alpha": 4.5,
        "cr_beta": 95.5,
        # Ticket promedio mas elevado (~$95 USD)
        "aov_mean": 95.0,
        "aov_sigma": 0.30,
        # Alta capacidad de escala en subasta
        "k_sat": 3800.0,
    },
    "tiktok": {
        "channel_id": CHANNEL_ENCODING["tiktok"],
        "weight": 0.15,  # 15% del volumen
        # Spend en 48h: LogNormal (~$30 a $350, media ~$90)
        "spend_mean_log": 4.40,
        "spend_sigma_log": 0.55,
        "spend_min": 20.0,
        # CPC barato por gran inventario de video (~$0.32)
        "cpc_base": 0.32,
        "cpc_sigma": 0.08,
        # Conversion baja/interrupcion rapida: Beta(2.0, 110.0) -> ~1.8%
        "cr_alpha": 2.0,
        "cr_beta": 110.0,
        # Ticket medio de impulso (~$45 USD)
        "aov_mean": 45.0,
        "aov_sigma": 0.22,
        # Saturacion mas rapida en creativos
        "k_sat": 1400.0,
    },
    "whatsapp": {
        "channel_id": CHANNEL_ENCODING["whatsapp"],
        "weight": 0.12,  # 12% del volumen
        # Spend en 48h: Mucho mas economico (costo por conversacion/plantilla Meta)
        # Gamma(shape=2.5, scale=8.0) -> ~$8 a $45, media ~$18
        "spend_mean_log": 2.80,
        "spend_sigma_log": 0.45,
        "spend_min": 5.0,
        # Costo por clic/interaccion interactiva (~$0.12)
        "cpc_base": 0.12,
        "cpc_sigma": 0.03,
        # Altisima conversion por conversacion personalizada: Beta(8.0, 92.0) -> ~8.0%
        "cr_alpha": 8.0,
        "cr_beta": 92.0,
        # Ticket promedio ~$60 USD
        "aov_mean": 60.0,
        "aov_sigma": 0.28,
        # Saturacion rapida de base de contactos (K_sat baja)
        "k_sat": 450.0,
    },
    "email": {
        "channel_id": CHANNEL_ENCODING["email"],
        "weight": 0.08,  # 8% del volumen
        # Spend en 48h: Costos fijos/marginales de plataforma (~$5 a $35)
        "spend_mean_log": 2.50,
        "spend_sigma_log": 0.40,
        "spend_min": 3.0,
        # Costo marginal por clic en newsletter (~$0.05)
        "cpc_base": 0.05,
        "cpc_sigma": 0.015,
        # Alta conversion de suscriptores/warm leads: Beta(7.0, 93.0) -> ~7.0%
        "cr_alpha": 7.0,
        "cr_beta": 93.0,
        # Ticket promedio medio-alto (~$75 USD)
        "aov_mean": 75.0,
        "aov_sigma": 0.30,
        # Se agota si se envian demasiados correos
        "k_sat": 350.0,
    },
    "organic": {
        "channel_id": CHANNEL_ENCODING["organic"],
        "weight": 0.05,  # 5% del volumen
        # Inversion monetaria minima o nula
        "spend_mean_log": 1.50,
        "spend_sigma_log": 0.50,
        "spend_min": 0.0,
        "cpc_base": 0.02,
        "cpc_sigma": 0.01,
        # Trafico de blog/SEO: Beta(2.5, 97.5) -> ~2.5%
        "cr_alpha": 2.5,
        "cr_beta": 97.5,
        "aov_mean": 55.0,
        "aov_sigma": 0.25,
        "k_sat": 150.0,
    },
    "direct": {
        "channel_id": CHANNEL_ENCODING["direct"],
        "weight": 0.05,  # 5% del volumen
        "spend_mean_log": 1.60,
        "spend_sigma_log": 0.45,
        "spend_min": 0.0,
        "cpc_base": 0.03,
        "cpc_sigma": 0.01,
        # Trafico de marca directo: Beta(3.5, 96.5) -> ~3.5%
        "cr_alpha": 3.5,
        "cr_beta": 96.5,
        "aov_mean": 65.0,
        "aov_sigma": 0.25,
        "k_sat": 200.0,
    },
}


def sample_synthetic_campaign(
    campaign_id: int,
    channel_name: Optional[str] = None,
    rng: Optional[random.Random] = None,
    np_rng: Optional[np.random.RandomState] = None,
) -> dict[str, Any]:
    """
    Genera una campana sintetica individual siguiendo las especificaciones
    economicas y de no linealidad (rendimientos decrecientes).
    """
    if rng is None:
        rng = random.Random()
    if np_rng is None:
        np_rng = np.random.RandomState()

    # Seleccionar canal segun pesos ponderados si no se especifica
    if not channel_name or channel_name not in CHANNEL_PROFILES:
        channel_names = list(CHANNEL_PROFILES.keys())
        weights = [CHANNEL_PROFILES[k]["weight"] for k in channel_names]
        channel_name = rng.choices(channel_names, weights=weights, k=1)[0]

    profile = CHANNEL_PROFILES[channel_name]

    # -------------------------------------------------------------------------
    # 1. spend_48h ~ Distribucion realista segun canal
    # -------------------------------------------------------------------------
    raw_spend = np_rng.lognormal(mean=profile["spend_mean_log"], sigma=profile["spend_sigma_log"])
    spend_48h = round(float(max(profile["spend_min"], raw_spend)), 2)

    # -------------------------------------------------------------------------
    # 2. clicks_48h = funcion de spend_48h con CPC variable por canal + ruido
    # -------------------------------------------------------------------------
    cpc_noise = max(0.01, np_rng.normal(profile["cpc_base"], profile["cpc_sigma"]))
    if spend_48h > 0:
        expected_clicks = spend_48h / cpc_noise
        # Ruido de poisson/normal segun escala de volumen
        click_noise = np_rng.normal(0.0, max(1.0, math.sqrt(expected_clicks) * 0.8))
        clicks_48h = max(1, int(round(expected_clicks + click_noise)))
    else:
        # Clics organicos base
        clicks_48h = int(np_rng.randint(30, 250))

    # -------------------------------------------------------------------------
    # 3. conversion_rate_48h ~ varia por canal + ruido
    # -------------------------------------------------------------------------
    base_cr = float(np_rng.beta(profile["cr_alpha"], profile["cr_beta"]))
    # Ruido adicional moderado
    cr_noise = float(np_rng.normal(0.0, 0.004))
    conversion_rate_48h = float(np.clip(base_cr + cr_noise, 0.002, 0.25))

    # -------------------------------------------------------------------------
    # 4. conversions_48h = clicks_48h * conversion_rate_48h
    # -------------------------------------------------------------------------
    # Muestreo binomial que produce distribucion probabilistica exacta
    conversions_48h = int(np_rng.binomial(clicks_48h, conversion_rate_48h))
    
    # Recalcular conversion_rate efectiva observada
    effective_cr_48h = round(conversions_48h / clicks_48h, 4) if clicks_48h > 0 else 0.0

    # -------------------------------------------------------------------------
    # 5. revenue_48h = conversions_48h * valor_promedio_por_conversion + ruido
    # -------------------------------------------------------------------------
    if conversions_48h > 0:
        # Cada conversion tiene un ticket individual lognormal
        individual_sales = [
            np_rng.lognormal(mean=math.log(profile["aov_mean"]), sigma=profile["aov_sigma"])
            for _ in range(conversions_48h)
        ]
        revenue_48h = round(float(sum(individual_sales)), 2)
    else:
        revenue_48h = 0.0

    # Duracion total de la campana en dias (de 7 a 45 dias)
    duration_days = int(rng.randint(7, 45))

    # -------------------------------------------------------------------------
    # 6. Relacion objetivo con rendimientos decrecientes (no lineal)
    #    roi_7d = f(spend_total_proyectado, canal, eficiencia_temprana) + ruido_final
    # -------------------------------------------------------------------------
    # a) Proyeccion de gasto total a 7 dias
    time_factor = min(duration_days, 7) / 2.0  # factor 3.5x para campanas >= 7 dias
    spend_total_proyectado = round(spend_48h * time_factor, 2)

    # b) Eficiencia temprana (Early ROAS y valor por clic)
    if spend_48h > 0:
        eficiencia_temprana = revenue_48h / spend_48h
    else:
        eficiencia_temprana = revenue_48h / max(1.0, clicks_48h * 0.05)

    # c) Funcion de saturacion no lineal (Curva Hill / Rendimientos Decrecientes)
    # A mayor gasto proyectado relativo a K_sat del canal, la eficiencia decae
    k_sat = profile["k_sat"]
    # Curva sigmoide/concava de saturacion: decay_factor en (0.2, 1.0)
    decay_factor = 1.0 / (1.0 + (spend_total_proyectado / k_sat) ** 0.85)

    # d) Gasto y revenue de los dias 3 a 7
    additional_spend = max(0.0, spend_total_proyectado - spend_48h)
    # La eficiencia marginal proyectada se ve impactada por la saturacion
    marginal_efficiency_noise = float(np_rng.normal(1.0, 0.06))
    marginal_roas = max(0.0, eficiencia_temprana * decay_factor * marginal_efficiency_noise)
    revenue_adicional = additional_spend * marginal_roas

    revenue_7d = revenue_48h + revenue_adicional

    # e) Calculo de roi_7d = (revenue_7d - spend_7d) / spend_7d + ruido_final
    if spend_total_proyectado > 0:
        roi_7d_base = (revenue_7d - spend_total_proyectado) / spend_total_proyectado
    else:
        # Para canales sin gasto directo (organico), se modela en torno al retorno sobre costo operativo nominal
        roi_7d_base = (revenue_7d - 10.0) / 10.0

    ruido_final = float(np_rng.normal(0.0, 0.05))
    roi_7d = round(float(np.clip(roi_7d_base + ruido_final, -1.0, 5.0)), 4)

    return {
        "id_campaign": campaign_id,
        "channel_name": channel_name,
        "channel_encoded": profile["channel_id"],
        "spend_48h": spend_48h,
        "clicks_48h": clicks_48h,
        "conversion_rate_48h": effective_cr_48h,
        "conversions_48h": conversions_48h,
        "revenue_48h": revenue_48h,
        "campaign_duration_days": duration_days,
        "spend_total_proyectado": spend_total_proyectado,
        "eficiencia_temprana": round(eficiencia_temprana, 4),
        "saturation_decay_factor": round(decay_factor, 4),
        "revenue_7d_proyectado": round(revenue_7d, 2),
        "roi_7d": roi_7d,
    }


def generate_synthetic_dataset(
    n: int = 500,
    seed: int = 42,
    channel_distribution: Optional[dict[str, int]] = None,
) -> list[dict[str, Any]]:
    """
    Genera un dataset de N campanas sinteticas detalladas como lista de diccionarios.
    """
    rng = random.Random(seed)
    np_rng = np.random.RandomState(seed)

    records: list[dict[str, Any]] = []

    if channel_distribution:
        # Generar segun cantidades explicitas por canal
        campaign_counter = 1
        for ch_name, count in channel_distribution.items():
            for _ in range(count):
                row = sample_synthetic_campaign(
                    campaign_id=campaign_counter,
                    channel_name=ch_name,
                    rng=rng,
                    np_rng=np_rng,
                )
                records.append(row)
                campaign_counter += 1
    else:
        for i in range(1, n + 1):
            row = sample_synthetic_campaign(
                campaign_id=i,
                rng=rng,
                np_rng=np_rng,
            )
            records.append(row)

    logger.info(f"Generado dataset sintetico de {len(records)} campanas (seed={seed}).")
    return records


def generate_synthetic_training_vectors(
    n: int = 200,
    seed: int = 42,
) -> list[tuple[list[float], float]]:
    """
    Genera vectores de entrenamiento directos (X, y) para compatibilidad con scikit-learn.
    X corresponde estrictamente a MODEL_FEATURE_COLUMNS y y a roi_7d.
    """
    dataset = generate_synthetic_dataset(n=n, seed=seed)
    training_data: list[tuple[list[float], float]] = []

    for row in dataset:
        X = [float(row[col]) for col in MODEL_FEATURE_COLUMNS]
        y = float(row["roi_7d"])
        training_data.append((X, y))

    return training_data


def save_dataset_to_csv(dataset: list[dict[str, Any]], filepath: str | Path) -> Path:
    """
    Exporta el dataset generado a un archivo CSV con todas las variables intermedias.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not dataset:
        raise ValueError("El dataset proporcionado esta vacio.")

    fieldnames = list(dataset[0].keys())

    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dataset)

    logger.info(f"Dataset exportado exitosamente a CSV: {path} ({len(dataset)} filas)")
    return path
