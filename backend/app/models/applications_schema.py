from typing import Optional, Literal
from pydantic import BaseModel

class ApplicationCreate(BaseModel):
    pet_id: str
    user_id: str
    full_name: str
    phone: str
    occupation: Optional[str] = None
    housing: Optional[str] = None
    has_experience: bool = False
    reason: Optional[str] = None

class PetSummary(BaseModel):
    name: str
    image: str

class Application(ApplicationCreate):
    id: str
    status: Literal['pending', 'approved', 'rejected']
    created_at: str
    pet: Optional[PetSummary] = None
