"""
app/ml/predictor_service.py
---------------------------
Servicio de inferencia singleton para el modelo Gradient Boosting.

El modelo se carga UNA SOLA VEZ al primer uso (lazy singleton) y
permanece en memoria para todos los requests subsiguientes.

NO se reentrena durante el ciclo de vida de una peticion HTTP.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ruta al artefacto serializado
# ---------------------------------------------------------------------------
ARTIFACTS_DIR = Path(__file__).parent / "model_artifacts"


def _find_latest_artifact() -> Optional[Path]:
    """
    Busca el artefacto .joblib mas reciente por numero de version en el nombre.
    Patron: gb_campaign_7d_v{N}.joblib
    """
    candidates = sorted(
        ARTIFACTS_DIR.glob("gb_campaign_7d_v*.joblib"),
        key=lambda p: _extract_version(p.name),
        reverse=True,
    )
    return candidates[0] if candidates else None


def _extract_version(filename: str) -> int:
    """Extrae el numero de version del nombre de archivo."""
    import re
    match = re.search(r"_v(\d+)\.joblib$", filename)
    return int(match.group(1)) if match else 0


# ---------------------------------------------------------------------------
# Singleton thread-safe
# ---------------------------------------------------------------------------

class _PredictorSingleton:
    """
    Contenedor thread-safe para el modelo cargado.
    Usa double-checked locking para evitar cargas dobles en
    entornos multi-hilo (e.g. uvicorn con workers).
    """

    _instance: Optional["_PredictorSingleton"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._model      = None
        self._metadata   = None
        self._artifact   = None
        self._load_lock  = threading.Lock()
        self._loaded     = False

    @classmethod
    def get_instance(cls) -> "_PredictorSingleton":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _load(self) -> None:
        """Carga el modelo desde disco (llamado una sola vez)."""
        import joblib  # import lazy para no forzar sklearn en modulos que no lo usan

        artifact_path = _find_latest_artifact()
        if artifact_path is None:
            raise FileNotFoundError(
                "No se encontro ningun modelo entrenado en "
                f"{ARTIFACTS_DIR}. Ejecuta: python -m app.ml.train_model"
            )

        logger.info(f"[PredictorService] Cargando modelo desde {artifact_path.name} …")
        bundle = joblib.load(artifact_path)
        self._model    = bundle["model"]
        self._metadata = {k: v for k, v in bundle.items() if k != "model"}
        self._artifact = artifact_path
        self._loaded   = True
        logger.info(
            f"[PredictorService] Modelo v{bundle.get('version', '?')} cargado. "
            f"Entrenado el {bundle.get('trained_at', 'desconocido')}. "
            f"MAE={bundle.get('metrics', {}).get('mae', '?'):.4f}"
        )

    def ensure_loaded(self) -> None:
        """Carga el modelo si aun no esta en memoria (thread-safe)."""
        if not self._loaded:
            with self._load_lock:
                if not self._loaded:
                    self._load()

    @property
    def model(self):
        self.ensure_loaded()
        return self._model

    @property
    def metadata(self) -> dict:
        self.ensure_loaded()
        return self._metadata or {}

    @property
    def artifact_name(self) -> str:
        self.ensure_loaded()
        return self._artifact.name if self._artifact else "unknown"

    @property
    def dataset_warning(self) -> Optional[str]:
        return self.metadata.get("dataset_warning")


# ---------------------------------------------------------------------------
# API publica del servicio
# ---------------------------------------------------------------------------

def predict_7d_roi(features: dict) -> float:
    """
    Predice el ROI a 7 dias dado el vector de features de una campana.

    Args:
        features: dict producido por build_features_from_campaign().
                  Se espera que contenga las claves de MODEL_FEATURE_COLUMNS.

    Returns:
        ROI predicho como float (e.g. 0.35 = 35% de ROI).

    Raises:
        FileNotFoundError: Si no hay modelo entrenado disponible.
    """
    from app.ml.feature_engineering import features_to_vector

    predictor = _PredictorSingleton.get_instance()
    X = [features_to_vector(features)]

    import numpy as np
    X_np = np.array(X, dtype=np.float32)
    prediction = predictor.model.predict(X_np)
    return float(prediction[0])


def get_model_metadata() -> dict:
    """Retorna metadatos del modelo cargado (version, metricas, etc.)."""
    return _PredictorSingleton.get_instance().metadata


def get_model_artifact_name() -> str:
    """Retorna el nombre del archivo del modelo activo."""
    return _PredictorSingleton.get_instance().artifact_name


def get_dataset_warning() -> Optional[str]:
    """Retorna el aviso de limitacion de datos (None si no aplica)."""
    return _PredictorSingleton.get_instance().dataset_warning
