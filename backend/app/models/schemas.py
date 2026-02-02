from typing import List, Optional, Literal, Union
from pydantic import BaseModel

class Owner(BaseModel):
    name: str # Keep for legacy/display compatibility
    role: str # Keep for compatibility
    image: str # Keep for compatibility

class UserBase(BaseModel):
    email: str
    name: Optional[str] = None
    role: str = "user"

class UserCreate(UserBase):
    password: str
    avatar_url: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class User(UserBase):
    id: str
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class HealthInfo(BaseModel):
    vaccinated: bool
    neutered: bool
    microchipped: bool
    chipNumber: Optional[str] = None

class Pet(BaseModel):
    id: str
    name: str
    breed: str
    age: str
    ageValue: int
    distance: str = "Unknown" # Placeholder as we don't have geo-calc yet
    image: str
    category: Literal['dog', 'cat', 'rabbit', 'other']
    price: Optional[str] = None
    gender: Optional[Literal['Male', 'Female']] = None
    weight: Optional[str] = None
    tags: Optional[List[str]] = []
    owner: Optional[Owner] = None
    health: Optional[HealthInfo] = None
    description: Optional[str] = None
    location: str

class PetCreate(BaseModel):
    name: str
    breed: str
    age_text: str
    age_value: int
    image_url: str
    category: str
    price: Optional[str] = None
    gender: Optional[str] = None
    weight: Optional[str] = None
    tags: Optional[List[str]] = []
    description: Optional[str] = None
    location: str
    health_info: Optional[dict] = None
    owner_id: str


class Message(BaseModel):
    id: str
    sender: Literal['user', 'coordinator']
    text: str
    timestamp: str
    isRead: Optional[bool] = False

class MessageCreate(BaseModel):
    conversation_id: str
    text: str
    sender_id: str # 'user' or uuid

class ChatSession(BaseModel):
    id: str
    petId: str
    petName: str
    petImage: str
    coordinatorName: str # Legacy, to be removed after frontend update
    coordinatorImage: str # Legacy, to be removed after frontend update
    otherParticipantName: str
    otherParticipantImage: str
    otherParticipantRole: str # 'coordinator' or 'user' (applicant)
    lastMessage: str
    lastMessageTime: str
    unreadCount: int = 0

class UserFavorite(BaseModel):
    user_id: str
    pet_id: str
