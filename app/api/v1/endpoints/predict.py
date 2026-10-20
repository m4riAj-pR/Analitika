"""
app/api/v1/endpoints/predict.py
--------------------------------
Endpoint de inferencia en tiempo real para predicción de ROI a 7 días y
proyección de ingresos publicitarios mediante Machine Learning.

Ruta:
    POST /api/v1/campaigns/predict-roi
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
import numpy as np
from pydantic import BaseModel, Field, field_validator

from app.ml.loader import get_roi_model

# ---------------------------------------------------------------------------
# Configuración del Logger de Auditoría y Monitoreo (Consola + Archivo Rotativo)
# ---------------------------------------------------------------------------
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_LOG_FILE = LOGS_DIR / "predictions.log"

audit_logger = logging.getLogger("analitika.ml.audit")
audit_logger.setLevel(logging.INFO)

# Evitar handlers duplicados si se recarga el módulo
if not audit_logger.handlers:
    # Formato uniforme para consola y archivo
    formatter = logging.Formatter(
        "%(asctime)s | [%(levelname)s] | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1. Consola (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    audit_logger.addHandler(console_handler)

    # 2. Archivo rotativo (máx 5MB por archivo, conserva 5 backups)
    file_handler = RotatingFileHandler(
        AUDIT_LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    audit_logger.addHandler(file_handler)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/campaigns", tags=["Predicciones ROI"])

# Canales admitidos y su codificación fija
CHANNEL_ENCODING: dict[str, int] = {
    "meta": 1,
    "facebook": 1,
    "google": 2,
    "tiktok": 3,
    "email": 4,
    "organic": 5,
    "direct": 6,
    "whatsapp": 7,
    "other": 0,
}


# ---------------------------------------------------------------------------
# Esquemas Pydantic
# ---------------------------------------------------------------------------

class PredictionInput(BaseModel):
    """
    Payload de entrada con las métricas observadas de la campaña en sus primeras 48 horas.
    """
    channel: str = Field(
        ...,
        description="Canal publicitario de la campaña: Meta, Google, WhatsApp, Email, TikTok",
        examples=["Meta"],
    )
    spend_48h: float = Field(
        ...,
        ge=0.0,
        description="Gasto/inversión publicitaria acumulada en las primeras 48 horas (USD o moneda base)",
        examples=[150.0],
    )
    clicks_48h: int = Field(
        ...,
        ge=0,
        description="Total de clics observados en los primeros 2 días",
        examples=[230],
    )
    conversions_48h: int = Field(
        ...,
        ge=0,
        description="Total de conversiones/leads/ventas registradas en las primeras 48h",
        examples=[12],
    )
    revenue_48h: float = Field(
        ...,
        ge=0.0,
        description="Ingreso total generado por las conversiones durante las primeras 48h",
        examples=[450.0],
    )

    @field_validator("channel")
    @classmethod
    def validate_and_normalize_channel(cls, v: str) -> str:
        cleaned = v.strip().lower()
        valid_channels = {"meta", "google", "whatsapp", "email", "tiktok"}
        if cleaned not in valid_channels:
            raise ValueError(
                f"Canal publicitario no válido: '{v}'. "
                f"Opciones permitidas: Meta, Google, WhatsApp, Email, TikTok."
            )
        # Normalizar a Title Case estándar
        mapping = {
            "meta": "Meta",
            "google": "Google",
            "whatsapp": "WhatsApp",
            "email": "Email",
            "tiktok": "TikTok",
        }
        return mapping[cleaned]


class PredictionOutput(BaseModel):
    """
    Resultado de la predicción de rendimiento financiero a 7 días y recomendación de decisión.
    """
    predicted_roi_7d: float = Field(
        ...,
        description="ROI predicho a 7 días en decimal (ej. 0.85 = +85% de retorno)",
        examples=[0.85],
    )
    estimated_revenue_7d: float = Field(
        ...,
        description="Ingreso proyectado acumulado a 7 días",
        examples=[1250.0],
    )
    strategic_recommendation: Literal[
        "Escalar presupuesto",
        "Mantener y monitorear",
        "Optimizar o pausar",
    ] = Field(
        ...,
        description="Acción estratégica recomendada basada en el ROI esperado",
        examples=["Escalar presupuesto"],
    )
    status: str = Field(
        default="success",
        description="Estado de la ejecución",
        examples=["success"],
    )


# ---------------------------------------------------------------------------
# Lógica de Negocio y Transformación de Features
# ---------------------------------------------------------------------------

def calculate_strategic_recommendation(predicted_roi: float) -> Literal[
    "Escalar presupuesto",
    "Mantener y monitorear",
    "Optimizar o pausar",
]:
    """
    Clasifica el ROI predicho en una recomendación de negocio accionable:
      - ROI >= +0.30 (+30% retorno neto): Escalar presupuesto
      - 0.0 <= ROI < +0.30 (Equilibrio a margen moderado): Mantener y monitorear
      - ROI < 0.0 (Pérdida neta proyectada): Optimizar o pausar
    """
    if predicted_roi >= 0.30:
        return "Escalar presupuesto"
    elif predicted_roi >= 0.0:
        return "Mantener y monitorear"
    else:
        return "Optimizar o pausar"


def estimate_7d_revenue(spend_48h: float, revenue_48h: float, predicted_roi: float) -> float:
    """
    Proyecta los ingresos a 7 días considerando el ritmo de gasto y el ROI predicho:
      - Factor temporal 48h -> 7d = 7 / 2 = 3.5x
      - Gasto proyectado 7d = spend_48h * 3.5
      - Ingreso proyectado 7d = gasto_7d * (1 + ROI_7d)
      - Si gasto es 0 (campaña orgánica/email sin pauta): revenue_48h * 3.5
    """
    if spend_48h > 0:
        projected_spend_7d = spend_48h * 3.5
        revenue_7d = projected_spend_7d * (1.0 + predicted_roi)
    else:
        revenue_7d = revenue_48h * 3.5

    return round(max(0.0, float(revenue_7d)), 2)


def build_input_vector(payload: PredictionInput) -> np.ndarray:
    """
    Construye el vector de características en el orden estricto esperado por el modelo:
      1. clicks_48h
      2. conversions_48h
      3. revenue_48h
      4. conversion_rate_48h
      5. spend_48h
      6. channel_encoded
      7. campaign_duration_days (7 días por estándar)
    """
    clicks = float(payload.clicks_48h)
    conversions = float(payload.conversions_48h)
    revenue = float(payload.revenue_48h)
    spend = float(payload.spend_48h)

    cr_48h = (conversions / clicks) if clicks > 0 else 0.0
    channel_key = payload.channel.strip().lower()
    channel_enc = float(CHANNEL_ENCODING.get(channel_key, 0))
    duration_days = 7.0

    features = [
        clicks,
        conversions,
        revenue,
        cr_48h,
        spend,
        channel_enc,
        duration_days,
    ]
    return np.array([features], dtype=np.float32)


# ---------------------------------------------------------------------------
# Endpoint de Inferencia
# ---------------------------------------------------------------------------

@router.post(
    "/predict-roi",
    response_model=PredictionOutput,
    status_code=status.HTTP_200_OK,
    summary="Predice el ROI a 7 días y genera recomendaciones estratégicas",
    description=(
        "Valida los datos observados de 48 horas de una campaña, ejecuta la inferencia "
        "con el modelo pre-cargado en memoria y devuelve el ROI esperado, los ingresos "
        "proyectados a 7 días y la acción recomendada de presupuesto."
    ),
)
def predict_campaign_roi(
    payload: PredictionInput,
    model: Any = Depends(get_roi_model),
) -> PredictionOutput:
    """
    Ejecuta la predicción del modelo Gradient Boosting para una campaña dada.
    
    1. Valida el payload de entrada contra el esquema `PredictionInput`.
    2. Construye el vector de features sin fugas de datos.
    3. Ejecuta `.predict()` sobre el pipeline/modelo cargado.
    4. Calcula la recomendación de negocio y proyección de ingresos.
    5. Registra la auditoría en consola y en `logs/predictions.log`.
    6. Retorna el resultado estructurado `PredictionOutput`.
    """
    start_time = datetime.now(timezone.utc)

    # 1. Transformación de features
    try:
        X_vec = build_input_vector(payload)
    except Exception as exc:
        logger.error(f"[Predict ROI] Error preparando vector de features: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en el preprocesamiento de métricas: {exc}",
        )

    # 2. Inferencia con el modelo inyectado
    try:
        raw_prediction = model.predict(X_vec)
        predicted_roi_raw = float(raw_prediction[0])
    except Exception as exc:
        logger.exception(f"[Predict ROI] Error en ejecución del modelo: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fallo al ejecutar la inferencia del modelo de Machine Learning.",
        )

    # 3. Postprocesamiento de negocio
    predicted_roi_7d = round(predicted_roi_raw, 2)
    recommendation = calculate_strategic_recommendation(predicted_roi_7d)
    estimated_revenue = estimate_7d_revenue(payload.spend_48h, payload.revenue_48h, predicted_roi_7d)

    # 4. Auditoría y monitoreo (Consola + Archivo)
    iso_timestamp = start_time.isoformat()
    audit_msg = (
        f"[AUDIT_PREDICTION] date={iso_timestamp} | channel={payload.channel} | "
        f"spend_48h={payload.spend_48h:.2f} | clicks_48h={payload.clicks_48h} | "
        f"conv_48h={payload.conversions_48h} | rev_48h={payload.revenue_48h:.2f} | "
        f"predicted_roi_7d={predicted_roi_7d:.2f} | est_rev_7d={estimated_revenue:.2f} | "
        f"recommendation='{recommendation}'"
    )
    audit_logger.info(audit_msg)

    # 5. Respuesta
    return PredictionOutput(
        predicted_roi_7d=predicted_roi_7d,
        estimated_revenue_7d=estimated_revenue,
        strategic_recommendation=recommendation,
        status="success",
    )
