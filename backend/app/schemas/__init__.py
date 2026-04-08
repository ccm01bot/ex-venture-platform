from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# Auth Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: UUID


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: Optional[str]
    role: str
    avatar_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Company Schemas
class CompanyCreate(BaseModel):
    name: str
    url: str
    industry_tags: Optional[List[str]] = None
    platform: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    industry_tags: Optional[List[str]] = None
    platform: Optional[str] = None
    base44_connected: Optional[bool] = None
    gsc_connected: Optional[bool] = None


class CompanyResponse(BaseModel):
    id: UUID
    name: str
    url: str
    industry_tags: List[str]
    platform: Optional[str]
    platform_confidence: Optional[float]
    base44_connected: bool
    gsc_connected: bool
    sitemaps_found: bool
    gsc_verified: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# SEO Scan Schemas
class SEOScanCreate(BaseModel):
    pass


class SEOScanResponse(BaseModel):
    id: UUID
    company_id: UUID
    overall_score: Optional[int]
    meta_score: Optional[int]
    content_score: Optional[int]
    technical_score: Optional[int]
    legal_score: Optional[int]
    pages_crawled: int
    urls_discovered: int
    healthy_pages: int
    impressum_found: bool
    privacy_found: bool
    terms_found: bool
    scanned_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Content Schemas
class ContentItemCreate(BaseModel):
    platform: str  # article, linkedin, instagram, facebook
    tone: str  # professional, casual, inspirational, technical, storytelling
    topic: str
    target_length: Optional[int] = None
    video_source_url: Optional[str] = None
    image_style: Optional[str] = None


class ContentItemResponse(BaseModel):
    id: UUID
    company_id: UUID
    platform: str
    tone: str
    topic: str
    target_length: Optional[int]
    content_body: Optional[str]
    image_url: Optional[str]
    status: str
    published_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Contact Schemas
class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    contact_type: str
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    job_title: Optional[str] = None
    organization: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class ContactResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    contact_type: str
    phone: Optional[str]
    job_title: Optional[str]
    organization: Optional[str]
    tags: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Outreach Campaign Schemas
class OutreachCampaignCreate(BaseModel):
    name: str
    campaign_type: str
    company_id: Optional[UUID] = None
    media_list_id: Optional[UUID] = None


class OutreachCampaignResponse(BaseModel):
    id: UUID
    name: str
    campaign_type: str
    status: str
    stats: dict
    created_at: datetime
    
    class Config:
        from_attributes = True


# Financial Account Schemas
class FinancialAccountCreate(BaseModel):
    account_name: str
    account_type: str
    currency: Optional[str] = "EUR"
    current_balance: float = 0.0
    institution: Optional[str] = None


class FinancialAccountResponse(BaseModel):
    id: UUID
    account_name: str
    account_type: str
    currency: str
    current_balance: float
    institution: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class FinancialTransactionCreate(BaseModel):
    account_id: UUID
    amount: float
    transaction_type: str
    category: str
    description: Optional[str] = None
    date: datetime


class FinancialTransactionResponse(BaseModel):
    id: UUID
    amount: float
    transaction_type: str
    category: str
    description: Optional[str]
    date: datetime
    
    class Config:
        from_attributes = True
