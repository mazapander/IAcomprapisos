import uuid
from typing import Literal

from pydantic import BaseModel, Field, model_validator


EventName = Literal[
    "page_view",
    "tool_selected",
    "location_selected",
    "wizard_step_completed",
    "budget_started",
    "budget_completed",
    "comparison_started",
    "comparison_completed",
    "review_started",
    "review_completed",
    "market_compared",
    "observatory_group_changed",
    "scenario_saved",
    "question_started",
    "question_submitted",
]

SAFE_PROPERTY_KEYS = {
    "geography_code",
    "result_status",
    "effort_bucket",
    "ltv_bucket",
    "alert_count_bucket",
    "source",
    "use_case",
    "step",
    "rate_type",
    "selection_method",
    "question_category",
    "limiting_factor",
    "offer_count_bucket",
}


class ConsentRequest(BaseModel):
    choice: Literal["accepted", "rejected"]
    consent_version: str = Field(default="2026-08", max_length=20)


class ProductEventRequest(BaseModel):
    event_name: EventName
    session_id: uuid.UUID
    page_path: str = Field(default="/", max_length=200, pattern=r"^/")
    properties: dict[str, str | int | bool] = Field(default_factory=dict)

    @model_validator(mode="after")
    def properties_are_safe(self):
        unknown = set(self.properties) - SAFE_PROPERTY_KEYS
        if unknown:
            raise ValueError(f"Unsupported analytics properties: {', '.join(sorted(unknown))}")
        if len(self.properties) > 8:
            raise ValueError("Too many analytics properties")
        for value in self.properties.values():
            if isinstance(value, str) and len(value) > 80:
                raise ValueError("Analytics property values are limited to 80 characters")
        return self


class QuestionRequest(BaseModel):
    question: str = Field(min_length=5, max_length=2000)
    category: Literal[
        "affordability",
        "offer",
        "mixed_mortgage",
        "early_repayment",
        "costs",
        "market",
        "process",
        "other",
    ] = "other"
    journey_stage: Literal["exploring", "comparing", "offer_received", "ready_to_sign"] = "exploring"
    geography_code: str | None = Field(default=None, max_length=20)
    contact_email: str | None = Field(
        default=None,
        max_length=254,
        pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$",
    )
    contact_consent: bool = False
    privacy_notice_accepted: Literal[True]
    privacy_notice_version: str = Field(default="2026-08", max_length=20)

    @model_validator(mode="after")
    def email_requires_contact_consent(self):
        if self.contact_email and not self.contact_consent:
            raise ValueError("Contact consent is required when an email is provided")
        return self


class QuestionNotificationResult(BaseModel):
    delivered: bool
    error: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def failed_delivery_requires_error(self):
        if not self.delivered and not self.error:
            raise ValueError("An error is required when delivery fails")
        return self
