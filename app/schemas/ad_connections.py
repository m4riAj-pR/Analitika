from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class AdProvider(str, Enum):
    META = "meta"
    GOOGLE = "google"
    TIKTOK = "tiktok"


class ConnectionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"


class AdConnectionPublic(BaseModel):
    """
    Representación pública de una conexión de cuenta publicitaria.
    CRÍTICO: Nunca expone access_token ni refresh_token.
    """
    id_connection: int
    id_company: int
    provider: AdProvider
    external_account_id: str
    account_name: Optional[str] = None
    status: ConnectionStatus
    status_message: Optional[str] = None
    connected_by: int
    connected_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OAuthConnectResponse(BaseModel):
    auth_url: str
    provider: str
    state: str


class ExternalCampaignItem(BaseModel):
    """Campaña obtenida de la API externa (Meta Ads Manager) para el selector de mapeo."""
    id: str
    name: str
    status: Optional[str] = None
    objective: Optional[str] = None


class CampaignExternalMappingCreate(BaseModel):
    id_connection: int
    external_campaign_id: str
    external_campaign_name: Optional[str] = None


class CampaignExternalMappingPublic(BaseModel):
    id_mapping: int
    id_campaign: int
    id_connection: int
    provider: str
    external_account_id: str
    external_campaign_id: str
    external_campaign_name: Optional[str] = None
    sync_enabled: bool = True
    created_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None


class CampaignExternalMetricPublic(BaseModel):
    id_metric: int
    id_mapping: int
    metric_date: str
    impressions: int
    spend: Decimal
    external_clicks: int
    reach: int
    fetched_at: Optional[datetime] = None


class SyncResultResponse(BaseModel):
    ok: bool
    id_connection: int
    synced_campaigns: int
    total_metrics_recorded: int
    errors: List[str] = []
