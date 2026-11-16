import pytest
from pydantic import ValidationError
from app.schemas import AdverseEventRequest

def valid_case():
    return {
        "case_id":"DEMO-101","drug_name":"DemoDrug",
        "reaction_description":"Skin peeling after medicine",
        "patient_age":45,"patient_sex":"female",
        "drug_start_date":"2026-11-01T09:00:00",
        "onset_date":"2026-11-08T09:00:00",
        "outcome":"hospitalisation","reporter_type":"doctor"
    }

def test_valid_case():
    assert AdverseEventRequest(**valid_case()).case_id == "DEMO-101"

def test_age_out_of_range():
    data=valid_case(); data["patient_age"]=150
    with pytest.raises(ValidationError):
        AdverseEventRequest(**data)

def test_onset_before_drug_start_rejected():
    data=valid_case(); data["onset_date"]="2026-10-30T09:00:00"
    with pytest.raises(ValidationError):
        AdverseEventRequest(**data)
