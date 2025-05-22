import os
import uuid

from app.auth.dependencies import authenticate_user
from app.database import get_async_session
from app.users.models import UsersDB
from app.users.utils import send_survey_contribution_email
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/contributions",
    tags=["contributions"],
)


@router.post("/submit")
async def contribute_survey(
    file: UploadFile = File(...),
    survey_title: str = Form(...),
    justification: str = Form(...),
    current_user: UsersDB = Depends(authenticate_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Submit a survey contribution for review.
    This will:
    1. Save the uploaded PDF file to a temporary location
    2. Send an email notification to the admin team
    3. Return a success message

    All user information is automatically extracted from the current user session.
    """
    # Validate file type
    if not file.content_type.lower() == "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted",
        )

    try:
        # Extract user information from the current session
        submitter_name = current_user.email.split("@")[0]  # Username from email
        submitter_email = current_user.email
        submitter_org = current_user.organization or "Not specified"
        user_id = current_user.user_id

        # Create a unique filename for the uploaded file
        filename = f"{uuid.uuid4().hex}_{file.filename}"

        # Create the contributions directory if it doesn't exist
        contributions_dir = os.path.join(os.getcwd(), "uploaded_contributions")
        os.makedirs(contributions_dir, exist_ok=True)

        # Save the file
        file_path = os.path.join(contributions_dir, filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Get admin email from environment variable or use a default
        admin_email = os.environ.get("ADMIN_EMAIL", "surveyaccelerator@idinsight.org")

        # Send email notification to admin using the existing email utility
        await send_survey_contribution_email(
            admin_email=admin_email,
            survey_title=survey_title,
            submitter_name=submitter_name,
            submitter_email=submitter_email,
            submitter_org=submitter_org,
            justification=justification,
            file_path=file_path,
            user_id=user_id,
        )

        return {
            "status": "success",
            "message": "Your survey contribution has been submitted for review. We'll get back to you soon.",
        }

    except Exception as e:
        # Log the exception
        print(f"Error processing survey contribution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process your contribution. Please try again later.",
        )
