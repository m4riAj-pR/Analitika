"""
app/routers/predictions.py
--------------------------
Router FastAPI para predicciones de ROI a 7 dias por campana.

Endpoint:
  GET /analitika/campaigns/{id_campaign}/predict

Protecciones:
  - Autenticacion JWT via get_current_user.
  - Restringido a roles Owner (2) y Super_Admin (1) via require_role([1, 2]).
  - Control de acceso por pertenencia via ensure_campaign_access().
  - Aviso explicito si la campana no tiene aun 48h de datos observados.
  - No se reentrena el modelo en ninguna peticion HTTP.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.db.database import run_query
from app.ml.feature_engineering import (
    OBSERVATION_WINDOW_HOURS,
    build_features_from_campaign,
)
from app.ml.predictor_service import (
    get_dataset_warning,
    get_model_artifact_name,
    get_model_metadata,
    predict_7d_roi,
)
from app.security import get_current_user, require_role
from app.services.a_service import ensure_campaign_access

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analitika", tags=["Predicciones ML"])


# ---------------------------------------------------------------------------
# Esquema de respuesta
# ---------------------------------------------------------------------------

class PredictionResponse(BaseModel):
    id_campaign:          int
    predicted_roi_7d:     float
    predicted_roi_7d_pct: str           # version legible, e.g. "34.52%"
    observation_window_hours: int       # siempre 48
    hours_of_data_available: float      # horas reales con datos al momento de predecir
    has_full_observation_window: bool   # True si ya pasaron las 48h
    low_confidence_warning: str | None  # aviso si hay <48h de datos
    dataset_warning:      str | None    # aviso si modelo fue entrenado con pocos datos reales
    model_artifact:       str           # nombre del archivo de modelo usado
    model_version:        int | None


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/campaigns/{id_campaign}/predict",
    response_model=PredictionResponse,
    summary="Predice el ROI a 7 dias de una campana",
    description=(
        "Estima el rendimiento financiero (ROI) de una campana a 7 dias "
        "usando datos observables en sus primeras 48 horas y un modelo "
        "Gradient Boosting pre-entrenado. "
        "Restringido a roles Owner y Super_Admin."
    ),
)
def predict_campaign_roi(
    id_campaign: int,
    current_user: dict = Depends(require_role([1, 2])),
) -> PredictionResponse:
    """
    Predice el ROI a 7 dias de la campana `id_campaign`.

    Flujo:
    1. Verifica autenticacion y rol (Owner o Super_Admin).
    2. Verifica acceso del usuario a la campana (pertenencia de empresa).
    3. Construye features de 48h con build_features_from_campaign().
    4. Llama al singleton PredictorService (modelo cargado una sola vez).
    5. Devuelve la prediccion con metadatos y avisos de confianza.
    """
    id_user = current_user["id_user"]
    id_role = current_user["id_role"]

    # ------------------------------------------------------------------
    # 1. Control de acceso por pertenencia de campana
    # ------------------------------------------------------------------
    try:
        ensure_campaign_access(id_user, id_campaign, id_role)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verificando acceso campana {id_campaign}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verificando acceso a la campana.",
        )

    # ------------------------------------------------------------------
    # 2. Construir features
    # ------------------------------------------------------------------
    try:
        features = build_features_from_campaign(id_campaign)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error construyendo features para campana {id_campaign}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error calculando features de la campana.",
        )

    # ------------------------------------------------------------------
    # 3. Aviso de confianza si <48h de datos
    # ------------------------------------------------------------------
    hours_elapsed = features.get("hours_elapsed", 0.0)
    has_full_window = features.get("has_full_observation_window", False)

    low_confidence_warning: str | None = None
    if not has_full_window:
        if hours_elapsed < 1:
            low_confidence_warning = (
                "La campana acaba de iniciar (menos de 1 hora de datos). "
                "La prediccion tiene muy baja confianza."
            )
        else:
            low_confidence_warning = (
                f"La campana solo tiene {hours_elapsed:.1f}h de datos "
                f"(ventana de observacion: {OBSERVATION_WINDOW_HOURS}h). "
                "La prediccion tiene menor confianza hasta completar 48h de datos."
            )

    # ------------------------------------------------------------------
    # 4. Predecir
    # ------------------------------------------------------------------
    try:
        roi = predict_7d_roi(features)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error en prediccion para campana {id_campaign}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error ejecutando la prediccion del modelo.",
        )

    # ------------------------------------------------------------------
    # 5. Metadatos del modelo
    # ------------------------------------------------------------------
    artifact_name = get_model_artifact_name()
    metadata = get_model_metadata()
    model_version = metadata.get("version")
    dataset_warning = get_dataset_warning()

    logger.info(
        f"[predict] campana={id_campaign} user={id_user} "
        f"roi={roi:.4f} hours={hours_elapsed:.1f} model={artifact_name}"
    )

    return PredictionResponse(
        id_campaign=id_campaign,
        predicted_roi_7d=round(roi, 6),
        predicted_roi_7d_pct=f"{roi * 100:.2f}%",
        observation_window_hours=OBSERVATION_WINDOW_HOURS,
        hours_of_data_available=round(hours_elapsed, 2),
        has_full_observation_window=has_full_window,
        low_confidence_warning=low_confidence_warning,
        dataset_warning=dataset_warning,
        model_artifact=artifact_name,
        model_version=model_version,
    )
