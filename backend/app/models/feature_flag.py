import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class FeatureFlagOverride(SQLModel, table=True):
    __tablename__ = "feature_flag_overrides"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    org_id: uuid.UUID = Field(foreign_key="organizations.id", index=True)
    flag_name: str
    enabled: bool
    updated_at: datetime = Field(default_factory=datetime.utcnow)
