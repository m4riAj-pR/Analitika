"""
tests/test_predict_roi_v1.py
----------------------------
Pruebas para el endpoint POST /api/v1/campaigns/predict-roi y el singleton de carga de modelo.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ml.loader import RoiModelSingleton, get_roi_model, load_roi_model
from app.api.v1.endpoints.predict import (
    calculate_strategic_recommendation,
    estimate_7d_revenue,
    PredictionInput,
)

client = TestClient(app)


def test_roi_model_singleton_loading():
    """Valida que el modelo se carga una sola vez y mantiene la misma instancia en memoria."""
    model_1 = load_roi_model()
    model_2 = get_roi_model()
    assert model_1 is not None
    assert model_1 is model_2
    assert RoiModelSingleton.get_instance().is_loaded is True


def test_strategic_recommendation_logic():
    """Valida los umbrales de negocio para la recomendación estratégica."""
    assert calculate_strategic_recommendation(0.55) == "Escalar presupuesto"
    assert calculate_strategic_recommendation(0.30) == "Escalar presupuesto"
    assert calculate_strategic_recommendation(0.15) == "Mantener y monitorear"
    assert calculate_strategic_recommendation(0.0) == "Mantener y monitorear"
    assert calculate_strategic_recommendation(-0.25) == "Optimizar o pausar"


def test_estimated_revenue_calculation():
    """Valida la proyección temporal e ingresos estimados a 7 días."""
    # spend=100 -> projected_spend_7d = 350. roi = 1.0 -> revenue = 350 * 2.0 = 700.0
    assert estimate_7d_revenue(100.0, 200.0, 1.0) == 700.0
    # spend=100 -> projected_spend_7d = 350. roi = -0.5 -> revenue = 350 * 0.5 = 175.0
    assert estimate_7d_revenue(100.0, 50.0, -0.5) == 175.0
    # spend=0 -> revenue_48h * 3.5 = 100 * 3.5 = 350.0
    assert estimate_7d_revenue(0.0, 100.0, 0.5) == 350.0


def test_predict_roi_endpoint_success_scaling():
    """Valida una predicción exitosa con recomendación de escalar."""
    payload = {
        "channel": "Meta",
        "spend_48h": 120.0,
        "clicks_48h": 250,
        "conversions_48h": 15,
        "revenue_48h": 500.0,
    }
    response = client.post("/api/v1/campaigns/predict-roi", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert isinstance(data["predicted_roi_7d"], float)
    assert isinstance(data["estimated_revenue_7d"], float)
    assert data["strategic_recommendation"] in [
        "Escalar presupuesto",
        "Mantener y monitorear",
        "Optimizar o pausar",
    ]


def test_predict_roi_endpoint_channel_case_insensitivity():
    """Valida que los nombres de canal sean normalizados correctamente."""
    for ch in ["meta", "GOOGLE", "WhatsApp", "email", "TikTok"]:
        payload = {
            "channel": ch,
            "spend_48h": 50.0,
            "clicks_48h": 100,
            "conversions_48h": 4,
            "revenue_48h": 120.0,
        }
        response = client.post("/api/v1/campaigns/predict-roi", json=payload)
        assert response.status_code == 200


def test_predict_roi_endpoint_validation_error_channel():
    """Valida el rechazo de canales no soportados."""
    payload = {
        "channel": "CanalInexistente",
        "spend_48h": 50.0,
        "clicks_48h": 100,
        "conversions_48h": 4,
        "revenue_48h": 120.0,
    }
    response = client.post("/api/v1/campaigns/predict-roi", json=payload)
    assert response.status_code == 422


def test_predict_roi_endpoint_validation_error_negative_values():
    """Valida el rechazo de valores negativos en métricas."""
    payload = {
        "channel": "Google",
        "spend_48h": -50.0,
        "clicks_48h": 100,
        "conversions_48h": 4,
        "revenue_48h": 120.0,
    }
    response = client.post("/api/v1/campaigns/predict-roi", json=payload)
    assert response.status_code == 422
