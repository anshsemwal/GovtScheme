from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
import json
from datetime import datetime
from .config import settings

# Create database and ensure directory exists
db_path = settings.database_url.replace("sqlite:///", "")
db_dir = os.path.dirname(db_path)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

SQLALCHEMY_DATABASE_URL = settings.database_url

# For SQLite we need this additional argument
connect_args = {"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class SavedScheme(Base):
    __tablename__ = "saved_schemes"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    scheme_id = Column(String)
    scheme_name = Column(String)
    scheme_category = Column(String, nullable=True)
    documents_required = Column(Text, nullable=True)
    saved_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "scheme_id": self.scheme_id,
            "scheme_name": self.scheme_name,
            "scheme_category": self.scheme_category,
            "saved_at": self.saved_at.isoformat() if self.saved_at else None
        }

class Application(Base):
    __tablename__ = "applications"
    STATUSES = ['draft', 'submitted', 'pending', 'approved', 'rejected']
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    scheme_id = Column(String)
    scheme_name = Column(String)
    status = Column(String, default='draft')
    notes = Column(Text, nullable=True)
    deadline = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "scheme_id": self.scheme_id,
            "scheme_name": self.scheme_name,
            "status": self.status,
            "notes": self.notes,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class FamilyMember(Base):
    __tablename__ = "family_members"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    name = Column(String)
    relation = Column(String)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    occupation = Column(String, nullable=True)
    is_disabled = Column(Boolean, default=False)
    is_student = Column(Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "relation": self.relation,
            "age": self.age,
            "gender": self.gender
        }

class UserProfile(Base):
    """Old profile model used by features_routes.py - linked by session_id"""
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    community = Column(String, nullable=True)
    state = Column(String, nullable=True)
    area_type = Column(String, nullable=True)
    occupation = Column(String, nullable=True)
    income = Column(Integer, nullable=True)
    family_size = Column(Integer, nullable=True)
    is_bpl = Column(Boolean, default=False)
    is_disabled = Column(Boolean, default=False)
    is_widow = Column(Boolean, default=False)
    is_senior = Column(Boolean, default=False)
    has_girl_child = Column(Boolean, default=False)
    language = Column(String, default='en')

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
