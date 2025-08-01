from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')

class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None

class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class DataResponse(BaseResponse, Generic[T]):
    """Generic data response model"""
    data: T

class PaginatedResponse(BaseResponse, Generic[T]):
    """Paginated response model"""
    data: List[T]
    total: int
    page: int = 1
    page_size: int = 100
    has_next: bool = False
    has_previous: bool = False

class AgentStatusResponse(BaseResponse):
    """Agent status response"""
    agent_type: str
    status: str  # "idle", "processing", "error"
    processing_time: Optional[float] = None
    
class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str] = Field(default_factory=dict)  # service_name -> status