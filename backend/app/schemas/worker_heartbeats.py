from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WorkerHeartbeatRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    worker_type: str
    worker_id: str
    status: str
    health_status: str
    last_heartbeat_at: datetime | None = None
    last_run_record_id: int | None = None
    last_run_mode: str = ""
    last_error: str = ""
    loops_completed: int
    metadata_payload: dict
    created_at: datetime | None = None
    updated_at: datetime | None = None
