from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import get_session
from models import Survey
from requests import SurveyCreateRequest, SurveyUpdateRequest
from responses import SurveyResponse, SurveyListResponse, MessageResponse

router = APIRouter(prefix="/api/surveys", tags=["Surveys"])


def _to_response(survey: Survey) -> SurveyResponse:
    data = survey.model_dump()
    data["liked_most"] = [item.strip() for item in survey.liked_most.split(",")]
    return SurveyResponse(**data)


@router.post(
    "",
    response_model=SurveyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new survey",
)
def create_survey(
    payload: SurveyCreateRequest,
    session: Session = Depends(get_session),
) -> SurveyResponse:
    survey = Survey(
        **payload.model_dump(exclude={"liked_most"}),
        liked_most=",".join(payload.liked_most),
    )
    session.add(survey)
    session.commit()
    session.refresh(survey)
    return _to_response(survey)


@router.get(
    "",
    response_model=SurveyListResponse,
    summary="Get all surveys",
)
def list_surveys(session: Session = Depends(get_session)) -> SurveyListResponse:
    surveys = session.exec(select(Survey)).all()
    return SurveyListResponse(
        total=len(surveys),
        surveys=[_to_response(s) for s in surveys],
    )


@router.get(
    "/{survey_id}",
    response_model=SurveyResponse,
    summary="Get a survey by ID",
)
def get_survey(
    survey_id: int,
    session: Session = Depends(get_session),
) -> SurveyResponse:
    survey = session.get(Survey, survey_id)
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Survey with id {survey_id} not found.",
        )
    return _to_response(survey)


@router.put(
    "/{survey_id}",
    response_model=SurveyResponse,
    summary="Update a survey",
)
def update_survey(
    survey_id: int,
    payload: SurveyUpdateRequest,
    session: Session = Depends(get_session),
) -> SurveyResponse:
    survey = session.get(Survey, survey_id)
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Survey with id {survey_id} not found.",
        )

    update_data = payload.model_dump(exclude_none=True)

    if "liked_most" in update_data:
        update_data["liked_most"] = ",".join(update_data["liked_most"])

    for field, value in update_data.items():
        setattr(survey, field, value)

    session.add(survey)
    session.commit()
    session.refresh(survey)
    return _to_response(survey)


@router.delete(
    "/{survey_id}",
    response_model=MessageResponse,
    summary="Delete a survey",
)
def delete_survey(
    survey_id: int,
    session: Session = Depends(get_session),
) -> MessageResponse:
    survey = session.get(Survey, survey_id)
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Survey with id {survey_id} not found.",
        )
    session.delete(survey)
    session.commit()
    return MessageResponse(message=f"Survey {survey_id} deleted successfully.")
