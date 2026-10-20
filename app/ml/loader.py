"""
app/ml/loader.py
----------------
Módulo singleton y gestor de ciclo de vida (lifespan) para la carga en memoria
del modelo de Machine Learning (`app/ml/model_roi_7d.joblib`).

Garantiza:
  - Carga única en memoria al iniciar el servidor (evita I/O disco en requests).
  - Acceso seguro en entornos concurrentes/multihilo (Double-Checked Locking).
  - Inyección de dependencias limpia para endpoints de FastAPI vía `Depends(get_roi_model)`.
  - Soporte tanto para `lifespan` de FastAPI como para eventos de startup y carga bajo demanda.
"""

from __future__ import annotations

import logging
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException, status
import joblib

logger = logging.getLogger("analitika.ml.loader")

# Ruta por defecto al modelo serializado
DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "model_roi_7d.joblib"
FALLBACK_MODEL_PATH = Path(__file__).resolve().parent / "model_artifacts" / "gb_campaign_7d_v1.joblib"


class RoiModelSingleton:
    """
    Contenedor singleton thread-safe para el modelo de predicción de ROI a 7 días.
    """

    _instance: Optional["RoiModelSingleton"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self._model: Any = None
        self._metadata: dict[str, Any] = {}
        self._model_path: Path = Path(os.getenv("ML_MODEL_PATH", str(DEFAULT_MODEL_PATH)))
        self._load_lock: threading.Lock = threading.Lock()
        self._is_loaded: bool = False

    @classmethod
    def get_instance(cls) -> "RoiModelSingleton":
        """Retorna la única instancia de RoiModelSingleton (Double-Checked Locking)."""
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def load(self, model_path: Optional[Path | str] = None) -> Any:
        """
        Carga el pipeline/modelo serializado en memoria si no está ya cargado.
        
        Args:
            model_path: Ruta opcional personalizada al archivo .joblib.
        """
        if self._is_loaded and self._model is not None:
            return self._model

        with self._load_lock:
            # Segunda comprobación tras adquirir el lock
            if self._is_loaded and self._model is not None:
                return self._model

            target_path = Path(model_path) if model_path else self._model_path

            # Fallback transparente si no se encuentra en la ruta directa
            if not target_path.exists():
                logger.warning(
                    f"[ML Loader] Modelo no encontrado en ruta principal: {target_path}. "
                    f"Comprobando ruta de respaldo: {FALLBACK_MODEL_PATH}"
                )
                if FALLBACK_MODEL_PATH.exists():
                    target_path = FALLBACK_MODEL_PATH
                else:
                    error_msg = (
                        f"Artefacto de modelo ML no encontrado ni en {target_path} "
                        f"ni en {FALLBACK_MODEL_PATH}. Ejecuta el script de entrenamiento previo."
                    )
                    logger.error(f"[ML Loader] {error_msg}")
                    raise FileNotFoundError(error_msg)

            logger.info(f"[ML Loader] Cargando modelo ML desde {target_path} ...")
            try:
                raw_artifact = joblib.load(target_path)
            except Exception as e:
                logger.exception(f"[ML Loader] Fallo crítico al deserializar artefacto joblib: {e}")
                raise RuntimeError(f"Error al deserializar modelo ML: {e}") from e

            # Si el artefacto fue empaquetado con metadatos como diccionario:
            if isinstance(raw_artifact, dict) and "model" in raw_artifact:
                self._model = raw_artifact["model"]
                self._metadata = {k: v for k, v in raw_artifact.items() if k != "model"}
            else:
                self._model = raw_artifact
                self._metadata = {}

            self._is_loaded = True
            self._model_path = target_path

            version = self._metadata.get("version", "1.0.0")
            trained_at = self._metadata.get("trained_at", "N/A")
            metrics = self._metadata.get("metrics", {})
            logger.info(
                f"[ML Loader] Modelo cargado exitosamente en RAM. "
                f"Versión: {version} | Fecha entrenamiento: {trained_at} | "
                f"Métricas registradas: {metrics} | Tipo: {type(self._model).__name__}"
            )

            return self._model

    def unload(self) -> None:
        """Libera la referencia del modelo para recolección de basura."""
        with self._load_lock:
            self._model = None
            self._metadata = {}
            self._is_loaded = False
            logger.info("[ML Loader] Modelo ML descargado de memoria.")

    def get_model(self) -> Any:
        """Obtiene el modelo cargado o lo carga si aún no está en memoria."""
        if not self._is_loaded or self._model is None:
            return self.load()
        return self._model

    @property
    def metadata(self) -> dict[str, Any]:
        """Metadatos asociados al artefacto entrenado."""
        return self._metadata

    @property
    def is_loaded(self) -> bool:
        """Estado de carga del modelo."""
        return self._is_loaded


# ---------------------------------------------------------------------------
# Funciones públicas y dependencias para FastAPI
# ---------------------------------------------------------------------------

def load_roi_model(model_path: Optional[Path | str] = None) -> Any:
    """Función de utilidad para precargar el modelo (por ejemplo, en startup)."""
    return RoiModelSingleton.get_instance().load(model_path=model_path)


def unload_roi_model() -> None:
    """Función de utilidad para descargar el modelo (por ejemplo, en shutdown)."""
    RoiModelSingleton.get_instance().unload()


def get_roi_model() -> Any:
    """
    Dependencia FastAPI (`Depends(get_roi_model)`).
    Devuelve la instancia del pipeline/modelo entrenado cargado en memoria.
    
    Raises:
        HTTPException 503 si el modelo no puede ser cargado o no está disponible.
    """
    try:
        model = RoiModelSingleton.get_instance().get_model()
        if model is None:
            raise RuntimeError("El modelo cargado es None")
        return model
    except Exception as exc:
        logger.error(f"[ML Loader] Error al resolver get_roi_model(): {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"El servicio de predicción ML no está listo o el modelo no está disponible: {exc}",
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gestor de contexto lifespan de FastAPI para cargar el modelo al arrancar
    y liberar recursos al apagar el servidor.
    
    Uso:
        app = FastAPI(lifespan=lifespan)
    """
    logger.info("[FastAPI lifespan] Inicializando servidor y precargando modelo ROI...")
    try:
        load_roi_model()
    except Exception as e:
        logger.error(f"[FastAPI lifespan] Advertencia: No se pudo precargar el modelo ML: {e}")
    
    yield
    
    logger.info("[FastAPI lifespan] Apagando servidor y liberando recursos ML...")
    unload_roi_model()
