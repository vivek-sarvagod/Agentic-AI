from datetime import date
from typing import List, Optional
from pydantic import BaseModel, EmailStr, field_validator

LIKED_MOST_OPTIONS = {"students", "location", "campus", "atmosphere", "dorm_rooms", "sports"}
INTEREST_SOURCE_OPTIONS = {"friends", "television", "internet", "other"}
RECOMMENDATION_OPTIONS = {"Very Likely", "Likely", "Unlikely"}


class SurveyCreateRequest(BaseModel):
    first_name: str
    last_name: str
    street_address: str
    city: str
    state: str
    zip_code: str
    telephone: str
    email: EmailStr
    date_of_survey: date
    liked_most: List[str]
    interest_source: str
    recommendation: str
    raffle: Optional[str] = None
    comments: Optional[str] = None

    @field_validator("liked_most")
    @classmethod
    def validate_liked_most(cls, v: List[str]) -> List[str]:
        invalid = set(v) - LIKED_MOST_OPTIONS
        if invalid:
            raise ValueError(
                f"Invalid liked_most values: {invalid}. "
                f"Allowed: {LIKED_MOST_OPTIONS}"
            )
        if not v:
            raise ValueError("liked_most must have at least one selection.")
        return v

    @field_validator("interest_source")
    @classmethod
    def validate_interest_source(cls, v: str) -> str:
        if v not in INTEREST_SOURCE_OPTIONS:
            raise ValueError(
                f"Invalid interest_source '{v}'. Allowed: {INTEREST_SOURCE_OPTIONS}"
            )
        return v

    @field_validator("recommendation")
    @classmethod
    def validate_recommendation(cls, v: str) -> str:
        if v not in RECOMMENDATION_OPTIONS:
            raise ValueError(
                f"Invalid recommendation '{v}'. Allowed: {RECOMMENDATION_OPTIONS}"
            )
        return v


class SurveyUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[EmailStr] = None
    date_of_survey: Optional[date] = None
    liked_most: Optional[List[str]] = None
    interest_source: Optional[str] = None
    recommendation: Optional[str] = None
    raffle: Optional[str] = None
    comments: Optional[str] = None

    @field_validator("liked_most")
    @classmethod
    def validate_liked_most(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        invalid = set(v) - LIKED_MOST_OPTIONS
        if invalid:
            raise ValueError(
                f"Invalid liked_most values: {invalid}. "
                f"Allowed: {LIKED_MOST_OPTIONS}"
            )
        if not v:
            raise ValueError("liked_most must have at least one selection.")
        return v

    @field_validator("interest_source")
    @classmethod
    def validate_interest_source(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in INTEREST_SOURCE_OPTIONS:
            raise ValueError(
                f"Invalid interest_source '{v}'. Allowed: {INTEREST_SOURCE_OPTIONS}"
            )
        return v

    @field_validator("recommendation")
    @classmethod
    def validate_recommendation(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in RECOMMENDATION_OPTIONS:
            raise ValueError(
                f"Invalid recommendation '{v}'. Allowed: {RECOMMENDATION_OPTIONS}"
            )
        return v
