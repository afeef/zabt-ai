from typing import List, Any
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.api import deps
from app.models import StyleProfile, StyleProfileCreate, User, StyleProfileRead
from app.services.styles import style_service, STYLES_DIR
import shutil

router = APIRouter()

@router.post("/", response_model=StyleProfileRead)
def create_style_profile(
    *,
    profile_in: StyleProfileCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new style profile.
    """
    profile = style_service.create_profile(profile_in, owner_id=current_user.id)
    return profile

@router.get("/", response_model=List[StyleProfileRead])
def read_style_profiles(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all style profiles for current user.
    """
    return style_service.get_profiles(owner_id=current_user.id)

@router.post("/upload_pdf", response_model=str)
async def upload_style_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Upload a PDF availability for parsing. 
    Returns extracted text to be used in 'prompt_template' or description.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
        
    file_location = STYLES_DIR / f"{current_user.id}_{file.filename}"
    try:
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
            
        text = style_service.parse_pdf(file_location)
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
