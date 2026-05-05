"""FastMCP tools for survey management."""
from datetime import date
from typing import List, Optional
from fastmcp import FastMCP
from sqlmodel import Session, select, or_

from database import get_session
from models import Survey


mcp = FastMCP("Student Survey Tools", port=8002)


def _format_survey(survey: Survey) -> dict:
    """Format a survey record for MCP tool output."""
    data = survey.model_dump()
    data["liked_most"] = [item.strip() for item in survey.liked_most.split(",")]
    if survey.raffle:
        data["raffle"] = [item.strip() for item in survey.raffle.split(",")]
    return data


@mcp.tool()
def create_survey(
    first_name: str,
    last_name: str,
    street_address: str,
    city: str,
    state: str,
    zip_code: str,
    telephone: str,
    email: str,
    date_of_survey: str,
    liked_most: List[str],
    interest_source: str,
    recommendation: str,
    raffle: Optional[List[str]] = None,
    comments: Optional[str] = None,
) -> dict:
    """Create a new student campus-visit survey record.
    
    Args:
        first_name: Student's first name
        last_name: Student's last name
        street_address: Street address
        city: City
        state: State
        zip_code: Zip/postal code
        telephone: Phone number
        email: Email address
        date_of_survey: Survey date in ISO format (YYYY-MM-DD)
        liked_most: List of what they liked (options: students, location, campus, atmosphere, dorm_rooms, sports)
        interest_source: How they became interested (options: friends, television, internet, other)
        recommendation: Likelihood to recommend (options: Very Likely, Likely, Unlikely)
        raffle: Optional list of raffle numbers (1-100)
        comments: Optional additional feedback
    
    Returns:
        Created survey record with assigned ID
    """
    session: Session = next(get_session())
    try:
        survey = Survey(
            first_name=first_name,
            last_name=last_name,
            street_address=street_address,
            city=city,
            state=state,
            zip_code=zip_code,
            telephone=telephone,
            email=email,
            date_of_survey=date.fromisoformat(date_of_survey),
            liked_most=",".join(liked_most),
            interest_source=interest_source,
            recommendation=recommendation,
            raffle=",".join(raffle) if raffle else None,
            comments=comments,
        )
        session.add(survey)
        session.commit()
        session.refresh(survey)
        return _format_survey(survey)
    finally:
        session.close()


@mcp.tool()
def list_surveys(limit: Optional[int] = None) -> dict:
    """List all survey records.
    
    Args:
        limit: Optional maximum number of records to return
    
    Returns:
        Dictionary with total count and list of surveys
    """
    session: Session = next(get_session())
    try:
        query = select(Survey)
        if limit:
            query = query.limit(limit)
        surveys = session.exec(query).all()
        return {
            "total": len(surveys),
            "surveys": [_format_survey(s) for s in surveys]
        }
    finally:
        session.close()


@mcp.tool()
def get_survey_by_id(survey_id: int) -> dict:
    """Get a specific survey by its ID.
    
    Args:
        survey_id: The unique ID of the survey
    
    Returns:
        Survey record details
    
    Raises:
        ValueError: If survey not found
    """
    session: Session = next(get_session())
    try:
        survey = session.get(Survey, survey_id)
        if not survey:
            raise ValueError(f"Survey with id {survey_id} not found")
        return _format_survey(survey)
    finally:
        session.close()


@mcp.tool()
def search_surveys(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    recommendation: Optional[str] = None,
) -> dict:
    """Search surveys by various criteria.
    
    Args:
        first_name: Filter by first name (partial match)
        last_name: Filter by last name (partial match)
        email: Filter by email (partial match)
        city: Filter by city (partial match)
        state: Filter by state (partial match)
        recommendation: Filter by recommendation level
    
    Returns:
        Dictionary with match count and list of matching surveys
    """
    session: Session = next(get_session())
    try:
        query = select(Survey)
        
        conditions = []
        if first_name:
            conditions.append(Survey.first_name.contains(first_name))
        if last_name:
            conditions.append(Survey.last_name.contains(last_name))
        if email:
            conditions.append(Survey.email.contains(email))
        if city:
            conditions.append(Survey.city.contains(city))
        if state:
            conditions.append(Survey.state.contains(state))
        if recommendation:
            conditions.append(Survey.recommendation == recommendation)
        
        if conditions:
            query = query.where(or_(*conditions))
        
        surveys = session.exec(query).all()
        return {
            "total": len(surveys),
            "surveys": [_format_survey(s) for s in surveys]
        }
    finally:
        session.close()


@mcp.tool()
def update_survey(
    survey_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    street_address: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None,
    telephone: Optional[str] = None,
    email: Optional[str] = None,
    date_of_survey: Optional[str] = None,
    liked_most: Optional[List[str]] = None,
    interest_source: Optional[str] = None,
    recommendation: Optional[str] = None,
    raffle: Optional[List[str]] = None,
    comments: Optional[str] = None,
) -> dict:
    """Update an existing survey record.
    
    Args:
        survey_id: The unique ID of the survey to update
        (all other fields optional - only provided fields will be updated)
    
    Returns:
        Updated survey record
    
    Raises:
        ValueError: If survey not found
    """
    session: Session = next(get_session())
    try:
        survey = session.get(Survey, survey_id)
        if not survey:
            raise ValueError(f"Survey with id {survey_id} not found")
        
        if first_name is not None:
            survey.first_name = first_name
        if last_name is not None:
            survey.last_name = last_name
        if street_address is not None:
            survey.street_address = street_address
        if city is not None:
            survey.city = city
        if state is not None:
            survey.state = state
        if zip_code is not None:
            survey.zip_code = zip_code
        if telephone is not None:
            survey.telephone = telephone
        if email is not None:
            survey.email = email
        if date_of_survey is not None:
            survey.date_of_survey = date.fromisoformat(date_of_survey)
        if liked_most is not None:
            survey.liked_most = ",".join(liked_most)
        if interest_source is not None:
            survey.interest_source = interest_source
        if recommendation is not None:
            survey.recommendation = recommendation
        if raffle is not None:
            survey.raffle = ",".join(raffle)
        if comments is not None:
            survey.comments = comments
        
        session.add(survey)
        session.commit()
        session.refresh(survey)
        return _format_survey(survey)
    finally:
        session.close()


@mcp.tool()
def delete_survey(survey_id: int) -> dict:
    """Delete a survey record.
    
    Args:
        survey_id: The unique ID of the survey to delete
    
    Returns:
        Success message
    
    Raises:
        ValueError: If survey not found
    """
    session: Session = next(get_session())
    try:
        survey = session.get(Survey, survey_id)
        if not survey:
            raise ValueError(f"Survey with id {survey_id} not found")
        
        session.delete(survey)
        session.commit()
        return {"message": f"Survey {survey_id} deleted successfully"}
    finally:
        session.close()
