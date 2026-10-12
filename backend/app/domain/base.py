"""
DentalAI - Base Domain Models
Common base classes and utilities for domain entities.
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID


class BaseEntity(BaseModel):
    """Base model for all database entities."""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True
    )


class TimestampedEntity(BaseEntity):
    """Entity with automatic timestamps."""
    
    created_at: datetime
    updated_at: datetime


class IdentifiedEntity(BaseEntity):
    """Entity with UUID identifier."""
    
    id: UUID
