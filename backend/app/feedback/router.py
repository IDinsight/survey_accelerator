"""This module contains the router for handling feedback submissions."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import authenticate_user
from app.database import get_async_session
from app.feedback.models import FeedbackDB
from app.feedback.schemas import FeedbackCreate, FeedbackResponse
from app.users.models import UsersDB
from app.utils import setup_logger

logger = setup_logger()

router = APIRouter(
    prefix="/feedback",
    tags=["feedback"],
)

TAG_METADATA = {
    "name": "Feedback",
    "description": "Endpoints for managing user feedback",
}


@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    current_user: UsersDB = Depends(authenticate_user),
    session: AsyncSession = Depends(get_async_session),
) -> FeedbackResponse:
    """
    Submit user feedback about search results.
    
    Args:
        feedback_data: The feedback data including type, comment and search_term
        current_user: The authenticated user
        session: The database session
        
    Returns:
        A success message and feedback ID
    """
    try:
        # Validate feedback_type
        if feedback_data.feedback_type not in ["like", "dislike"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Feedback type must be either 'like' or 'dislike'",
            )
            
        # Create feedback record
        new_feedback = FeedbackDB(
            user_id=current_user.user_id,
            feedback_type=feedback_data.feedback_type,
            comment=feedback_data.comment,
            search_term=feedback_data.search_term
        )
        
        session.add(new_feedback)
        await session.commit()
        await session.refresh(new_feedback)
        
        logger.info(f"Feedback submitted by user {current_user.user_id}: {feedback_data.feedback_type} for search: '{feedback_data.search_term}'")
        
        return FeedbackResponse(
            message="Feedback submitted successfully",
            feedback_id=new_feedback.feedback_id
        )
        
    except Exception as e:
        await session.rollback()
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}",
        )