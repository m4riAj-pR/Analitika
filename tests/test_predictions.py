"""
tests/test_predictions.py
-------------------------
Pruebas unitarias y de integracion para el modulo de ML de Analitika:
- Feature engineering y vectorizacion
- Generacion de datos sinteticos
- Inferencia mediante PredictorService
- Endpoint GET /analitika/campaigns/{id_campaign}/predict
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.ml.feature_engineering import (
    MODEL_FEATURE_COLUMNS,
    features_to_vector,
    _encode_channel,
)
from app.ml.predictor_service import (
    _extract_version,
    predict_7d_roi,
    get_model_metadata,
)
from app.ml.train_model import generate_synthetic_data
from app.main import app


def test_channel_encoding():
    assert _encode_channel("meta") == 1
    assert _encode_channel("Facebook") == 1
    assert _encode_channel("google") == 2
    assert _encode_channel("TikTok") == 3
    assert _encode_channel("unknown_channel") == 0
    assert _encode_channel(None) == 0


def test_features_to_vector():
    sample_features = {
        "clicks_48h": 150,
        "conversions_48h": 5,
        "revenue_48h": 350.5,
        "conversion_rate_48h": 5 / 150,
        "spend_48h": 120.0,
        "channel_encoded": 1,
        "campaign_duration_days": 14,
    }
    vector = features_to_vector(sample_features)
    assert len(vector) == len(MODEL_FEATURE_COLUMNS)
    assert vector[0] == 150.0
    assert vector[1] == 5.0
    assert vector[2] == 350.5
    assert vector[4] == 120.0
    assert vector[5] == 1.0
    assert vector[6] == 14.0


def test_synthetic_data_generation():
    records = generate_synthetic_data(n=20, seed=123)
    assert len(records) == 20
    for X, y in records:
        assert len(X) == len(MODEL_FEATURE_COLUMNS)
        assert isinstance(y, float)


def test_extract_version():
    assert _extract_version("gb_campaign_7d_v1.joblib") == 1
    assert _extract_version("gb_campaign_7d_v12.joblib") == 12
    assert _extract_version("random_name.joblib") == 0


def test_predict_endpoint_unauthorized():
    client = TestClient(app)
    response = client.get("/analitika/campaigns/1/predict")
    assert response.status_code == 401


def test_predict_endpoint_forbidden_role():
    client = TestClient(app)
    from app.security import get_current_user
    fake_token_data = {"id_user": 99, "id_role": 3, "email": "viewer@test.com"}
    app.dependency_overrides[get_current_user] = lambda: fake_token_data
    try:
        response = client.get(
            "/analitika/campaigns/1/predict",
            headers={"Authorization": "Bearer fake_token"}
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_predict_endpoint_success():
    client = TestClient(app)
    from app.security import get_current_user
    fake_user = {"id_user": 1, "id_role": 1, "email": "admin@test.com"}
    fake_features = {
        "id_campaign": 1,
        "clicks_48h": 200,
        "conversions_48h": 10,
        "revenue_48h": 500.0,
        "conversion_rate_48h": 0.05,
        "spend_48h": 150.0,
        "channel_encoded": 1,
        "campaign_duration_days": 10,
        "has_full_observation_window": True,
        "hours_elapsed": 48.0,
        "start_date": "2026-01-01",
    }

    app.dependency_overrides[get_current_user] = lambda: fake_user
    try:
        with patch("app.routers.predictions.ensure_campaign_access", return_value=None), \
             patch("app.routers.predictions.build_features_from_campaign", return_value=fake_features):
            response = client.get(
                "/analitika/campaigns/1/predict",
                headers={"Authorization": "Bearer valid_token"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "predicted_roi_7d" in data
            assert "predicted_roi_7d_pct" in data
            assert data["id_campaign"] == 1
            assert data["has_full_observation_window"] is True
            assert data["observation_window_hours"] == 48
            assert data["model_version"] == 1
    finally:
        app.dependency_overrides.clear()
