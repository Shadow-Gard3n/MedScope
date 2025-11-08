from pydantic import BaseModel
from typing import List


class PredictionInput(BaseModel):
    age_grp: str
    sex: str
    reporter_country: str
    occr_country: str
    is_hcp: bool
    drug_profile_joined: str


class AvoidAlternativesInput(BaseModel):
    indication: str
    avoid_side_effects: list[str]
    original_drug_name: str = ""

class SearchAlternativesInput(BaseModel):
    drug_name: str = ""
    indication: str = ""


class ChatInput(BaseModel):
    message: str