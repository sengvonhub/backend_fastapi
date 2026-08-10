from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.company import CompanyStatus


class CompanyStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    old_status: CompanyStatus
    new_status: CompanyStatus
    reason: Optional[str] = None
    changed_by: int
    changed_at: datetime