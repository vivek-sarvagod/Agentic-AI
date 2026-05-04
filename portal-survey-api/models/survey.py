from datetime import date
from typing import Optional
from sqlmodel import Field, SQLModel


class Survey(SQLModel, table=True):
    __tablename__ = "surveys"

    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    street_address: str = Field(max_length=255)
    city: str = Field(max_length=100)
    state: str = Field(max_length=50)
    zip_code: str = Field(max_length=10)
    telephone: str = Field(max_length=20)
    email: str = Field(max_length=150)
    date_of_survey: date

    # What they liked most (comma-separated values from allowed options)
    liked_most: str = Field(
        max_length=255,
        description="Comma-separated: students, location, campus, atmosphere, dorm_rooms, sports",
    )

    # How they became interested
    interest_source: str = Field(
        max_length=50,
        description="One of: friends, television, internet, other",
    )

    # Likelihood of recommendation
    recommendation: str = Field(
        max_length=20,
        description="One of: Very Likely, Likely, Unlikely",
    )

    # Raffle numbers (comma-separated, optional)
    raffle: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Comma-separated raffle numbers (1-100)",
    )

    # Additional comments (optional)
    comments: Optional[str] = Field(
        default=None,
        description="Additional feedback or comments",
    )
