"""Database models for Art Studio Companion."""

from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/art_studio.db")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Supply(Base):
    """Art supply inventory item."""
    __tablename__ = "supplies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(255))
    category = Column(String(100))  # paint, brush, canvas, paper, etc.
    color = Column(String(100))  # for paints/inks
    size = Column(String(50))  # brush size, canvas dimensions, etc.
    quantity = Column(Float, default=1.0)  # 1.0 = full, 0.5 = half, etc.
    unit = Column(String(50))  # tube, bottle, sheet, piece
    notes = Column(Text)
    image_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to usage history
    usage_history = relationship("SupplyUsage", back_populates="supply")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "brand": self.brand,
            "category": self.category,
            "color": self.color,
            "size": self.size,
            "quantity": self.quantity,
            "unit": self.unit,
            "notes": self.notes,
            "status": self.get_status(),
            "image_path": self.image_path,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def get_status(self):
        """Return color-coded status based on quantity."""
        if self.quantity >= 0.5:
            return "green"  # plenty
        elif self.quantity >= 0.25:
            return "yellow"  # low
        else:
            return "red"  # empty/critical


class SupplyUsage(Base):
    """Track supply usage per project."""
    __tablename__ = "supply_usage"

    id = Column(Integer, primary_key=True, index=True)
    supply_id = Column(Integer, ForeignKey("supplies.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    quantity_used = Column(Float)
    used_at = Column(DateTime, default=datetime.utcnow)

    supply = relationship("Supply", back_populates="usage_history")
    project = relationship("Project", back_populates="supplies_used")


class Project(Base):
    """Art project with plans and materials."""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="planned")  # planned, in_progress, completed
    medium = Column(String(100))  # watercolor, oil, acrylic, etc.
    style = Column(String(100))  # landscape, portrait, abstract, etc.
    estimated_budget = Column(Float)
    actual_budget = Column(Float)
    materials_list = Column(Text)  # JSON string of required materials
    steps = Column(Text)  # JSON string of project steps
    notes = Column(Text)
    file_path = Column(String(500))  # path to saved project file
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    supplies_used = relationship("SupplyUsage", back_populates="project")
    portfolio_pieces = relationship("PortfolioPiece", back_populates="project")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "medium": self.medium,
            "style": self.style,
            "estimated_budget": self.estimated_budget,
            "materials_list": self.materials_list,
            "steps": self.steps,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class PortfolioPiece(Base):
    """Artwork in the portfolio."""
    __tablename__ = "portfolio_pieces"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    project_id = Column(Integer, ForeignKey("projects.id"))
    status = Column(String(50), default="sketch")  # sketch, wip, completed
    medium = Column(String(100))
    dimensions = Column(String(100))  # e.g., "8x10 inches"
    image_path = Column(String(500))  # main image
    thumbnail_path = Column(String(500))
    progress_images = Column(Text)  # JSON array of progress image paths
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    project = relationship("Project", back_populates="portfolio_pieces")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "project_id": self.project_id,
            "status": self.status,
            "medium": self.medium,
            "dimensions": self.dimensions,
            "image_path": self.image_path,
            "thumbnail_path": self.thumbnail_path,
            "progress_images": self.progress_images,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class StylePreference(Base):
    """User's style preferences inferred from Pinterest and chat."""
    __tablename__ = "style_preferences"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100))  # color_palette, brushwork, subject, mood
    value = Column(String(255))
    confidence = Column(Float, default=0.5)  # 0-1 confidence score
    source = Column(String(100))  # pinterest, chat, explicit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "value": self.value,
            "confidence": self.confidence,
            "source": self.source
        }


class ChatHistory(Base):
    """Store chat history for context."""
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(50))  # user, assistant
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Initialize the database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
