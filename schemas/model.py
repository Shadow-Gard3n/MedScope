from pydantic import BaseModel


class PredictionInput(BaseModel):
    age_grp: str
    sex: str
    reporter_country: str
    occr_country: str
    is_hcp: bool
    age_in_years: float
    drug_profile_joined: str 