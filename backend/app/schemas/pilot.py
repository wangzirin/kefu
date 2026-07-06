from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


PilotReadinessStatusPattern = (
    "^(blocked|pilot_candidate_ready_with_internal_data|pilot_candidate_ready_with_customer_data)$"
)


class PilotReadinessStepRead(BaseModel):
    code: str
    title: str
    status: str
    summary: str
    next_action: str
    target_href: str
    blockers: list[str] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)


class PilotRuntimeFactRead(BaseModel):
    fact_key: str
    status: str
    source: str
    evidence_path: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    not_ready_for: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CustomerMaterialBatchRead(BaseModel):
    id: int
    batch_code: str
    status: str
    material_row_count: int
    question_count: int
    record_type_coverage: list[str] = Field(default_factory=list)
    question_action_coverage: list[str] = Field(default_factory=list)
    blocker_count: int
    desensitization_risk_count: int
    created_at: datetime


class CustomerMaterialBatchListRead(BaseModel):
    schema_version: str
    tenant_id: int
    generated_at: datetime
    status: str
    summary: str
    batches: list[CustomerMaterialBatchRead]
    latest_batch: CustomerMaterialBatchRead | None = None
    counts: dict[str, int] = Field(default_factory=dict)
    readiness: dict[str, Any] = Field(default_factory=dict)
    safety: dict[str, Any] = Field(default_factory=dict)
    next_steps: list[str] = Field(default_factory=list)


class PilotReadinessRead(BaseModel):
    schema_version: str
    tenant_id: int
    generated_at: datetime
    status: str = Field(pattern=PilotReadinessStatusPattern)
    status_label: str
    summary: str
    steps: list[PilotReadinessStepRead]
    blockers: list[str]
    evidence_links: list[dict[str, Any]]
    not_ready_for: list[str]
    safety: dict[str, Any]
    recommended_next_steps: list[str]
    trial_closure_status: str = "not_evaluated"
    trial_closure_evidence: list[dict[str, Any]] = Field(default_factory=list)
    handoff_archive_status: str = "not_generated"
    pack8_status: str = "not_generated"
    pack8_evidence: list[dict[str, Any]] = Field(default_factory=list)
    material_intake_package_status: str = "not_checked"
    material_intake_package_evidence: list[dict[str, Any]] = Field(default_factory=list)
    material_validation_fixture_status: str = "not_checked"
    material_validation_fixture_evidence: list[dict[str, Any]] = Field(default_factory=list)
    material_drop_gate_status: str = "not_checked"
    material_drop_gate_evidence: list[dict[str, Any]] = Field(default_factory=list)
    real_customer_material_status: str = "not_checked"
    real_customer_material_evidence: list[dict[str, Any]] = Field(default_factory=list)
    customer_knowledge_retest_status: str = "not_checked"
    customer_knowledge_retest_evidence: list[dict[str, Any]] = Field(default_factory=list)
    shadow_trial_status: str = "not_checked"
    shadow_trial_evidence: list[dict[str, Any]] = Field(default_factory=list)
    frontend_customer_qa_status: str = "not_checked"
    frontend_customer_qa_evidence: list[dict[str, Any]] = Field(default_factory=list)
    frontend_product_polish_status: str = "not_checked"
    frontend_product_polish_evidence: list[dict[str, Any]] = Field(default_factory=list)
    channel_boundary_status: str = "not_checked"
    channel_boundary_evidence: list[dict[str, Any]] = Field(default_factory=list)
    installer_trial_status: str = "not_checked"
    installer_trial_evidence: list[dict[str, Any]] = Field(default_factory=list)
    pack10_status: str = "not_generated"
    pack10_evidence: list[dict[str, Any]] = Field(default_factory=list)
    runtime_facts: list[PilotRuntimeFactRead] = Field(default_factory=list)
    latest_material_batch: CustomerMaterialBatchRead | None = None
    customer_data_ready: bool = False
    customer_data_readiness_source: str = "database_fact_chain"
    customer_data_ready_blockers: list[str] = Field(default_factory=list)
    customer_data_ready_evidence: list[dict[str, Any]] = Field(default_factory=list)
    summary_evidence_authority: str = "engineering_evidence_only"


class KnowledgeConfirmationImportCreate(BaseModel):
    filename: str = Field(default="customer_knowledge_confirmation.csv", max_length=240)
    csv_text: str = Field(min_length=1, max_length=400000)


class KnowledgeConfirmationImportItemRead(BaseModel):
    item_id: str
    section: str
    item_name: str
    review_status: str
    confirmed_by: str
    confirmed_at: str
    reviewer_role: str
    customer_comment: str
    needs_change: bool
    blockers: list[str] = Field(default_factory=list)


class KnowledgeConfirmationImportRead(BaseModel):
    schema_version: str
    tenant_id: int
    imported_at: datetime
    filename: str
    status: str
    summary: str
    total_rows: int
    confirmed_count: int
    needs_revision_count: int
    rejected_count: int
    pending_count: int
    accepted_with_notes_count: int
    revision_items: list[KnowledgeConfirmationImportItemRead]
    rejected_items: list[KnowledgeConfirmationImportItemRead]
    pending_items: list[KnowledgeConfirmationImportItemRead]
    blockers: list[str]
    desensitization_risks: list[str]
    ready_for_next_retest: bool
    formal_customer_signoff_ready: bool
    system_prefilled_customer_confirmation: bool
    safety: dict[str, Any]


class CustomerMaterialPrecheckCreate(BaseModel):
    materials_csv: str = Field(min_length=1, max_length=800000)
    trial_questions_csv: str = Field(min_length=1, max_length=800000)
    manifest_json: str = Field(min_length=1, max_length=200000)


class CustomerMaterialPrecheckRead(BaseModel):
    schema_version: str
    tenant_id: int
    checked_at: datetime
    status: str
    summary: str
    blockers: list[str]
    metrics: dict[str, Any]
    readiness: dict[str, Any]
    safety: dict[str, Any]
    persisted_batch: CustomerMaterialBatchRead | None = None


class SafeTestConversationRead(BaseModel):
    schema_version: str
    tenant_id: int
    conversation_id: int
    message_id: int
    channel_id: int
    contact_id: int
    target_href: str
    summary: str
    external_write_performed: bool = False
    safety: dict[str, Any] = Field(default_factory=dict)


class CustomerMaterialTemplatePackageRead(BaseModel):
    schema_version: str
    tenant_id: int
    generated_at: datetime
    status: str
    summary: str
    materials_template_csv: str
    trial_questions_template_csv: str
    manifest_template_json: str
    sample_materials_csv: str
    sample_trial_questions_csv: str
    sample_manifest_json: str
    required_received_filenames: dict[str, str]
    field_guide: list[dict[str, Any]]
    next_steps: list[str]
    readiness: dict[str, Any]
    safety: dict[str, Any]


class CustomerMaterialHandoffBundleRead(BaseModel):
    schema_version: str
    tenant_id: int
    generated_at: datetime
    status: str
    summary: str
    filename: str
    content_type: str
    body_encoding: str
    body: str
    included_files: list[str]
    required_received_filenames: dict[str, str]
    next_steps: list[str]
    readiness: dict[str, Any]
    safety: dict[str, Any]
