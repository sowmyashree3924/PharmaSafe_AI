from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator

class AdverseEventRequest(BaseModel):
    case_id: str = Field(..., min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    drug_name: str = Field(..., min_length=2, max_length=150)
    reaction_description: str = Field(..., min_length=5, max_length=3000)
    patient_age: int = Field(..., ge=0, le=120)
    patient_sex: Literal["female", "male", "other", "unknown"]
    onset_date: datetime
    drug_start_date: datetime
    outcome: Literal[
        "recovered", "recovering", "not_recovered", "fatal",
        "hospitalisation", "disability", "congenital_anomaly", "unknown"
    ]
    reporter_type: Literal["doctor", "pharmacist", "patient", "literature", "other"] = "other"

    @model_validator(mode="after")
    def check_dates(self):
        if self.onset_date < self.drug_start_date:
            raise ValueError("onset_date cannot be earlier than drug_start_date")
        return self

class FeedbackRequest(BaseModel):
    satisfactory: bool
    reason: str = Field(..., min_length=3, max_length=1000)
