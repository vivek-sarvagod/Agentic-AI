from datetime import date
from typing import List
from pydantic import BaseModel


class SurveyResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    street_address: str
    city: str
    state: str
    zip_code: str
    telephone: str
    email: str
    date_of_survey: date
    liked_most: List[str]
    interest_source: str
    recommendation: str
    raffle: str | None = None
    comments: str | None = None

    model_config = {"from_attributes": True}


class SurveyListResponse(BaseModel):
    total: int
    surveys: List[SurveyResponse]


class MessageResponse(BaseModel):
    message: str
