import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Enum, ForeignKeyConstraint, JSON
# PostgreSQL UUID - using String for SQLite compat
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class RoleEnum(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    editor = "editor"
    viewer = "viewer"


class SeverityEnum(str, enum.Enum):
    critical = "critical"
    warning = "warning"
    info = "info"


class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.owner)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    companies = relationship("Company", back_populates="user", cascade="all, delete-orphan")
    content_items = relationship("ContentItem", back_populates="user", cascade="all, delete-orphan")
    youtube_channels = relationship("YouTubeChannel", back_populates="user", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="user", cascade="all, delete-orphan")
    outreach_campaigns = relationship("OutreachCampaign", back_populates="user", cascade="all, delete-orphan")
    financial_accounts = relationship("FinancialAccount", back_populates="user", cascade="all, delete-orphan")


class Company(Base):
    __tablename__ = "companies"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    name = Column(String, nullable=False, index=True)
    url = Column(String, nullable=False)
    industry_tags = Column(JSON, default=list)
    platform = Column(String, nullable=True)
    platform_confidence = Column(Float, nullable=True)
    cms_platform = Column(String, default="none")
    cms_url = Column(String, nullable=True)
    cms_api_key = Column(String, nullable=True)
    base44_connected = Column(Boolean, default=False)
    gsc_connected = Column(Boolean, default=False)
    sitemaps_found = Column(Boolean, default=False)
    gsc_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="companies")
    seo_scans = relationship("SEOScan", back_populates="company", cascade="all, delete-orphan")
    seo_issues = relationship("SEOIssue", back_populates="company", cascade="all, delete-orphan")
    content_items = relationship("ContentItem", back_populates="company", cascade="all, delete-orphan")
    outreach_campaigns = relationship("OutreachCampaign", back_populates="company")
    financial_transactions = relationship("FinancialTransaction", back_populates="company")
    financial_accounts = relationship("FinancialAccount", back_populates="company")


class SEOScan(Base):
    __tablename__ = "seo_scans"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    overall_score = Column(Integer, nullable=True)
    meta_score = Column(Integer, nullable=True)
    content_score = Column(Integer, nullable=True)
    technical_score = Column(Integer, nullable=True)
    legal_score = Column(Integer, nullable=True)
    pages_crawled = Column(Integer, default=0)
    urls_discovered = Column(Integer, default=0)
    healthy_pages = Column(Integer, default=0)
    page_types = Column(Integer, default=0)
    impressum_found = Column(Boolean, default=False)
    privacy_found = Column(Boolean, default=False)
    terms_found = Column(Boolean, default=False)
    impressum_completeness = Column(Float, nullable=True)
    privacy_completeness = Column(Float, nullable=True)
    terms_completeness = Column(Float, nullable=True)
    raw_results = Column(JSON, nullable=True)
    scanned_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    company = relationship("Company", back_populates="seo_scans")
    issues = relationship("SEOIssue", back_populates="scan", cascade="all, delete-orphan")


class SEOIssue(Base):
    __tablename__ = "seo_issues"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String(36), ForeignKey("seo_scans.id"), nullable=False, index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    severity = Column(Enum(SeverityEnum), nullable=False)
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    page_url = Column(String, nullable=True)
    resolved = Column(Boolean, default=False)
    
    scan = relationship("SEOScan", back_populates="issues")
    company = relationship("Company", back_populates="seo_issues")


class ContentItem(Base):
    __tablename__ = "content_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    platform = Column(String, nullable=False)  # article, linkedin, instagram, facebook
    tone = Column(String, nullable=False)
    topic = Column(Text, nullable=False)
    target_length = Column(Integer, nullable=True)  # 300, 500, 800, 1200, 2000
    video_source_url = Column(String, nullable=True)
    content_body = Column(Text, nullable=True)
    content_html = Column(Text, nullable=True)
    image_style = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    user_photos = Column(JSON, default=list)
    status = Column(String, default="draft")  # draft, published, archived
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company = relationship("Company", back_populates="content_items")
    user = relationship("User", back_populates="content_items")


class YouTubeChannel(Base):
    __tablename__ = "youtube_channels"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    channel_id = Column(String, nullable=False, unique=True)
    channel_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    subscribers = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    video_count = Column(Integer, default=0)
    avg_views = Column(Integer, default=0)
    est_daily_views = Column(Integer, default=0)
    outlier_videos = Column(Integer, default=0)
    underperforming = Column(Integer, default=0)
    upload_frequency_days = Column(Integer, nullable=True)
    avg_duration_seconds = Column(Integer, nullable=True)
    last_refreshed = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="youtube_channels")
    videos = relationship("YouTubeVideo", back_populates="channel", cascade="all, delete-orphan")


class YouTubeVideo(Base):
    __tablename__ = "youtube_videos"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    channel_id = Column(String(36), ForeignKey("youtube_channels.id"), nullable=False, index=True)
    video_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    duration_seconds = Column(Integer, nullable=True)
    published_at = Column(DateTime, nullable=True)
    seo_score = Column(Integer, nullable=True)
    optimized_title = Column(String, nullable=True)
    optimized_description = Column(Text, nullable=True)
    optimized_tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    channel = relationship("YouTubeChannel", back_populates="videos")


class YouTubeSEOJob(Base):
    __tablename__ = "youtube_seo_jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    video_url = Column(String, nullable=True)
    script_text = Column(Text, nullable=True)
    input_type = Column(String, nullable=False)  # url, script, file
    file_url = Column(String, nullable=True)
    results = Column(JSON, nullable=True)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)


class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    twitter_handle = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    organization = Column(String, nullable=True)
    contact_type = Column(String, nullable=False)  # journalist, partner, investor, lead, influencer, other
    tags = Column(JSON, default=list)
    notes = Column(Text, nullable=True)
    last_contacted = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="contacts")
    company = relationship("Company")
    media_list_memberships = relationship("MediaListContact", back_populates="contact")
    outreach_messages = relationship("OutreachMessage", back_populates="contact")


class MediaList(Base):
    __tablename__ = "media_lists"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    list_type = Column(String, nullable=False)  # journalists, bloggers, influencers, partners, custom
    created_at = Column(DateTime, default=datetime.utcnow)
    
    contacts = relationship("MediaListContact", back_populates="media_list", cascade="all, delete-orphan")


class MediaListContact(Base):
    __tablename__ = "media_list_contacts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    media_list_id = Column(String(36), ForeignKey("media_lists.id"), nullable=False)
    contact_id = Column(String(36), ForeignKey("contacts.id"), nullable=False)
    
    media_list = relationship("MediaList", back_populates="contacts")
    contact = relationship("Contact", back_populates="media_list_memberships")


class OutreachCampaign(Base):
    __tablename__ = "outreach_campaigns"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=True)
    name = Column(String, nullable=False)
    campaign_type = Column(String, nullable=False)  # email_cold, email_linkbuild, linkedin, twitter, pr_pitch, multi_channel
    status = Column(String, default="draft")  # draft, active, paused, completed, archived
    media_list_id = Column(String(36), ForeignKey("media_lists.id"), nullable=True)
    settings = Column(JSON, default=dict)
    stats = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="outreach_campaigns")
    company = relationship("Company", back_populates="outreach_campaigns")
    sequences = relationship("OutreachSequence", back_populates="campaign", cascade="all, delete-orphan")
    messages = relationship("OutreachMessage", back_populates="campaign", cascade="all, delete-orphan")


class OutreachSequence(Base):
    __tablename__ = "outreach_sequences"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String(36), ForeignKey("outreach_campaigns.id"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    channel = Column(String, nullable=False)  # email, linkedin, twitter
    delay_days = Column(Integer, default=0)
    subject_template = Column(String, nullable=True)
    body_template = Column(Text, nullable=False)
    is_ai_generated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    campaign = relationship("OutreachCampaign", back_populates="sequences")
    messages = relationship("OutreachMessage", back_populates="sequence")


class OutreachMessage(Base):
    __tablename__ = "outreach_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sequence_id = Column(String(36), ForeignKey("outreach_sequences.id"), nullable=False, index=True)
    campaign_id = Column(String(36), ForeignKey("outreach_campaigns.id"), nullable=False, index=True)
    contact_id = Column(String(36), ForeignKey("contacts.id"), nullable=False, index=True)
    channel = Column(String, nullable=False)  # email, linkedin, twitter
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=False)
    status = Column(String, default="scheduled")  # scheduled, sent, delivered, opened, clicked, replied, bounced, failed
    sent_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    replied_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sequence = relationship("OutreachSequence", back_populates="messages")
    campaign = relationship("OutreachCampaign", back_populates="messages")
    contact = relationship("Contact", back_populates="outreach_messages")


class PressRelease(Base):
    __tablename__ = "press_releases"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    distribution_list_id = Column(String(36), ForeignKey("media_lists.id"), nullable=True)
    status = Column(String, default="draft")  # draft, review, approved, distributed
    distributed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FinancialAccount(Base):
    __tablename__ = "financial_accounts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=True)
    account_name = Column(String, nullable=False)
    account_type = Column(String, nullable=False)  # business_bank, investment, real_estate, crypto, other
    currency = Column(String, default="EUR")
    current_balance = Column(Float, default=0.0)
    institution = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="financial_accounts")
    company = relationship("Company", back_populates="financial_accounts")
    transactions = relationship("FinancialTransaction", back_populates="account", cascade="all, delete-orphan")


class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = Column(String(36), ForeignKey("financial_accounts.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False)  # income, expense, transfer, investment
    category = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    account = relationship("FinancialAccount", back_populates="transactions")
    company = relationship("Company", back_populates="financial_transactions")


class ReportSnapshot(Base):
    __tablename__ = "report_snapshots"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    report_type = Column(String, nullable=False)  # seo_portfolio, financial_summary, outreach_performance, youtube_analytics, full_overview
    data = Column(JSON, nullable=True)
    generated_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
